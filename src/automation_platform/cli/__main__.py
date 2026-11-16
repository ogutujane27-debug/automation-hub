"""Command-line interface for the automation platform."""

import argparse
import json
import signal
import sys
from threading import Event

from ..runtime import AutomationPlatform
from ..bootstrap import load_jobs
from ..scheduler.engine import SchedulerEngine
from ..scheduler.service import SchedulerService


def build_parser():
    parser = argparse.ArgumentParser(
        prog="automation-platform",
        description="Manage and operate registered automations.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List registered automations")

    run_parser = subparsers.add_parser("run", help="Execute an automation")
    run_parser.add_argument("job_name")
    run_parser.add_argument("--trigger", default="manual")

    history_parser = subparsers.add_parser(
        "history", help="Show execution history"
    )
    history_parser.add_argument("--job", dest="job_name")
    history_parser.add_argument("--limit", type=int, default=20)

    show_parser = subparsers.add_parser(
        "show", help="Show details of one execution"
    )
    show_parser.add_argument("run_id")

    subparsers.add_parser("healthcheck", help="Check platform health")

    scheduler_parser = subparsers.add_parser(
        "scheduler", help="Run the continuous automation scheduler"
    )
    scheduler_parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Seconds between scheduler checks (default: 1.0)",
    )

    return parser


def run_scheduler(platform, poll_interval):
    stop_event = Event()
    engine = SchedulerEngine(platform)
    service = SchedulerService(engine, poll_interval=poll_interval)

    previous_handlers = {}

    def request_shutdown(signum, frame):
        stop_event.set()

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, request_shutdown)

        print("Automation scheduler started. Press Ctrl+C to stop.")
        print(f"Polling interval: {service.poll_interval:g} seconds")
        print(f"Loaded schedules: {len(engine.list_schedules())}")

        service.run_forever(stop_event)

    except KeyboardInterrupt:
        stop_event.set()
        print("\nScheduler shutdown requested.")

    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)

    print("Automation scheduler stopped.")
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scheduler":
        try:
            platform = load_jobs(AutomationPlatform())
            return run_scheduler(platform, args.poll_interval)
        except ValueError as exc:
            parser.error(str(exc))

    platform = load_jobs(AutomationPlatform())

    if args.command == "list":
        jobs = platform.list_jobs()

        if not jobs:
            print("No automations are currently registered.")
            return 0

        for job in jobs:
            print(f"{job.name} - {job.description}")

        return 0

    if args.command == "run":
        try:
            result = platform.run_job(
                name=args.job_name,
                trigger=args.trigger,
            )
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        print(json.dumps({
            "run_id": result.run_id,
            "job_name": result.job_name,
            "status": result.status,
            "trigger": result.trigger,
            "duration_seconds": result.duration_seconds,
            "output": result.output,
            "error_type": result.error_type,
            "error_message": result.error_message,
        }, indent=2, default=str))

        return 0 if result.status == "succeeded" else 1

    if args.command == "history":
        if args.limit < 1:
            parser.error("--limit must be at least 1")

        runs = platform.list_runs(
            job_name=args.job_name,
            limit=args.limit,
        )

        if not runs:
            print("No execution history found.")
            return 0

        for run in runs:
            print(
                f"{run.started_at.isoformat()} | "
                f"{run.job_name} | {run.status} | "
                f"{run.trigger} | {run.run_id}"
            )

        return 0

    if args.command == "show":
        result = platform.get_run(args.run_id)

        if result is None:
            print(f"Execution not found: {args.run_id}", file=sys.stderr)
            return 1

        print(json.dumps({
            "run_id": result.run_id,
            "job_name": result.job_name,
            "status": result.status,
            "trigger": result.trigger,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "duration_seconds": result.duration_seconds,
            "output": result.output,
            "error_type": result.error_type,
            "error_message": result.error_message,
        }, indent=2, default=str))

        return 0

    if args.command == "healthcheck":
        try:
            platform.history_store.list_runs(limit=1)
            print("Platform: OK")
            print("History storage: OK")
            return 0
        except Exception as exc:
            print("Platform: DEGRADED")
            print(f"History storage: ERROR ({type(exc).__name__})")
            return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
