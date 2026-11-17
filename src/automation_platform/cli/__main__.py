"""Command-line interface for the automation platform."""

import argparse
import json
import signal
import sys
from datetime import time
from threading import Event

from ..runtime import AutomationPlatform
from ..bootstrap import load_jobs
from ..scheduler.engine import SchedulerEngine
from ..scheduler.models import ScheduleDefinition
from ..scheduler.service import SchedulerService
from ..api.server import run_server


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

    serve_parser = subparsers.add_parser(
        "serve", help="Start the HTTP API and automation scheduler"
    )
    serve_parser.add_argument(
        "--host", default="127.0.0.1",
        help="HTTP server host (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000,
        help="HTTP server port (default: 8000)",
    )
    serve_parser.add_argument(
        "--poll-interval", type=float, default=1.0,
        help="Seconds between scheduler checks (default: 1.0)",
    )

    schedule_parser = subparsers.add_parser(
        "schedule", help="Manage automation schedules"
    )
    schedule_subparsers = schedule_parser.add_subparsers(
        dest="schedule_action", required=True
    )

    schedule_list_parser = schedule_subparsers.add_parser(
        "list", help="List active and paused schedules"
    )
    schedule_list_parser.add_argument("--job", dest="job_name")

    schedule_add_parser = schedule_subparsers.add_parser(
        "add", help="Create an automation schedule"
    )
    schedule_add_parser.add_argument("job_name")
    schedule_add_parser.add_argument(
        "--frequency", required=True,
        choices=["interval", "daily", "weekly"]
    )
    schedule_add_parser.add_argument(
        "--interval-seconds", type=int
    )
    schedule_add_parser.add_argument("--run-time")
    schedule_add_parser.add_argument(
        "--weekdays",
        help="Comma-separated weekdays for weekly schedules"
    )

    for action in ("pause", "resume", "remove"):
        action_parser = schedule_subparsers.add_parser(
            action, help=f"{action.capitalize()} a schedule"
        )
        action_parser.add_argument("schedule_id")

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


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def handle_schedule_command(platform, args):
    engine = SchedulerEngine(platform)
    store = platform.schedule_store

    if args.schedule_action == "list":
        schedules = store.list_schedules(enabled_only=False)

        if args.job_name:
            schedules = [
                row for row in schedules
                if row["job_name"] == args.job_name
            ]

        if not schedules:
            print("No schedules found.")
            return 0

        for row in schedules:
            status = "active" if row["enabled"] else "paused"
            print(
                f"{row['schedule_id']} | "
                f"{row['job_name']} | "
                f"{row['frequency']} | "
                f"{status} | "
                f"Next run: {row['next_run_at'] or 'Not scheduled'}"
            )

        return 0

    if args.schedule_action == "add":
        try:
            if args.frequency == "interval":
                if (
                    args.interval_seconds is None
                    or args.interval_seconds <= 0
                    or args.run_time is not None
                    or args.weekdays is not None
                ):
                    raise ValueError(
                        "Interval schedules require a positive "
                        "--interval-seconds and do not accept "
                        "--run-time or --weekdays."
                    )

                schedule = ScheduleDefinition(
                    job_name=args.job_name,
                    frequency="interval",
                    interval_seconds=args.interval_seconds,
                )

            elif args.frequency == "daily":
                if (
                    args.run_time is None
                    or args.interval_seconds is not None
                    or args.weekdays is not None
                ):
                    raise ValueError(
                        "Daily schedules require --run-time HH:MM "
                        "and do not accept --interval-seconds or --weekdays."
                    )

                schedule = ScheduleDefinition(
                    job_name=args.job_name,
                    frequency="daily",
                    run_time=time.fromisoformat(args.run_time),
                )

            else:
                if (
                    args.run_time is None
                    or args.weekdays is None
                    or args.interval_seconds is not None
                ):
                    raise ValueError(
                        "Weekly schedules require --run-time HH:MM "
                        "and --weekdays."
                    )

                weekday_names = [
                    name.strip().lower()
                    for name in args.weekdays.split(",")
                ]

                if (
                    not weekday_names
                    or any(name not in WEEKDAYS for name in weekday_names)
                ):
                    raise ValueError(
                        "Invalid weekday. Use monday,tuesday,wednesday,"
                        "thursday,friday,saturday,sunday."
                    )

                weekdays = tuple(WEEKDAYS[name] for name in weekday_names)

                if len(set(weekdays)) != len(weekdays):
                    raise ValueError("Weekdays must not contain duplicates.")

                schedule = ScheduleDefinition(
                    job_name=args.job_name,
                    frequency="weekly",
                    run_time=time.fromisoformat(args.run_time),
                    weekdays=weekdays,
                )

            engine.add_schedule(schedule)

        except (ValueError, KeyError) as exc:
            print(f"Unable to add schedule: {exc}", file=sys.stderr)
            return 1

        print(f"Schedule created: {schedule.schedule_id}")
        return 0

    if args.schedule_action == "pause":
        if engine.pause_schedule(args.schedule_id):
            print(f"Schedule paused: {args.schedule_id}")
            return 0

        print(
            f"Unable to pause schedule: {args.schedule_id}",
            file=sys.stderr,
        )
        return 1

    if args.schedule_action == "resume":
        try:
            resumed = engine.resume_schedule(args.schedule_id)
        except (ValueError, KeyError) as exc:
            print(f"Unable to resume schedule: {exc}", file=sys.stderr)
            return 1

        if resumed:
            print(f"Schedule resumed: {args.schedule_id}")
            return 0

        print(
            f"Unable to resume schedule: {args.schedule_id}",
            file=sys.stderr,
        )
        return 1

    if args.schedule_action == "remove":
        if engine.remove_schedule(args.schedule_id):
            print(f"Schedule removed: {args.schedule_id}")
            return 0

        print(
            f"Schedule not found: {args.schedule_id}",
            file=sys.stderr,
        )
        return 1

    return 1


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        try:
            platform = load_jobs(AutomationPlatform())
            return run_server(
                platform,
                host=args.host,
                port=args.port,
                poll_interval=args.poll_interval,
            )
        except ValueError as exc:
            parser.error(str(exc))

    if args.command == "scheduler":
        try:
            platform = load_jobs(AutomationPlatform())
            return run_scheduler(platform, args.poll_interval)
        except ValueError as exc:
            parser.error(str(exc))

    platform = load_jobs(AutomationPlatform())

    if args.command == "schedule":
        return handle_schedule_command(platform, args)

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
