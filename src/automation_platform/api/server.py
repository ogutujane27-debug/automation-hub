"""HTTP server and scheduler startup for the automation platform."""

import signal
from threading import Event, Thread
from wsgiref.simple_server import make_server

from ..scheduler.engine import SchedulerEngine
from ..scheduler.service import SchedulerService
from .health import create_app


def run_server(
    platform,
    host: str = "127.0.0.1",
    port: int = 8000,
    poll_interval: float = 1.0,
) -> int:
    """Run the HTTP API and scheduler using one shared platform."""

    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")

    stop_event = Event()

    engine = SchedulerEngine(platform)
    scheduler = SchedulerService(
        engine,
        poll_interval=poll_interval,
    )

    http_server = make_server(
        host,
        port,
        create_app(platform),
    )
    http_server.timeout = 0.5

    scheduler_thread = Thread(
        target=scheduler.run_forever,
        args=(stop_event,),
        name="automation-scheduler",
        daemon=False,
    )

    previous_handlers = {}

    def request_shutdown(signum, frame):
        stop_event.set()

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, request_shutdown)

        scheduler_thread.start()

        print(f"Automation API listening on http://{host}:{port}")
        print(f"Health endpoint: http://{host}:{port}/healthz")
        print(f"Loaded schedules: {len(engine.list_schedules())}")
        print("Press Ctrl+C to stop.")

        while not stop_event.is_set():
            http_server.handle_request()

    except KeyboardInterrupt:
        stop_event.set()
        print("\nShutdown requested.")

    finally:
        stop_event.set()

        if scheduler_thread.is_alive():
            scheduler_thread.join()

        http_server.server_close()

        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)

    print("Automation platform stopped.")
    return 0
