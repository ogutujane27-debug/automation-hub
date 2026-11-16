"""Scheduler engine for due automation jobs."""

import json
from datetime import datetime, time, timezone

from .clock import next_run_time
from .models import ScheduleDefinition
from .registry import ScheduleRegistry


class SchedulerEngine:

    def __init__(self, platform, registry=None, store=None):
        self.platform = platform
        self.registry = registry or ScheduleRegistry()
        self.store = (
            store if store is not None
            else getattr(platform, "schedule_store", None)
        )
        self._next_runs: dict[str, datetime] = {}

        if self.store is not None:
            self.load_schedules()

    def add_schedule(self, schedule: ScheduleDefinition) -> None:
        self.platform.registry.get(schedule.job_name)

        next_run = next_run_time(schedule, datetime.now(timezone.utc))
        self.registry.register(schedule)

        try:
            if self.store is not None:
                self.store.save(schedule, next_run)

            self._next_runs[schedule.schedule_id] = next_run
        except Exception:
            self.registry.remove(schedule.schedule_id)
            raise

    def load_schedules(self) -> None:
        if self.store is None:
            return

        for row in self.store.list_schedules(enabled_only=True):
            schedule = ScheduleDefinition(
                job_name=row["job_name"],
                frequency=row["frequency"],
                interval_seconds=row["interval_seconds"],
                run_time=(
                    time.fromisoformat(row["run_time"])
                    if row["run_time"] else None
                ),
                weekdays=tuple(json.loads(row["weekdays_json"])),
                schedule_id=row["schedule_id"],
            )

            self.platform.registry.get(schedule.job_name)
            next_run = datetime.fromisoformat(row["next_run_at"])

            self.registry.register(schedule)
            self._next_runs[schedule.schedule_id] = next_run

    def list_schedules(self) -> list[ScheduleDefinition]:
        return self.registry.list_schedules()

    def pause_schedule(self, schedule_id: str) -> bool:
        if self.store is None:
            return False

        try:
            self.registry.get(schedule_id)
        except KeyError:
            return False

        if not self.store.set_enabled(schedule_id, False):
            return False

        self.registry.remove(schedule_id)
        self._next_runs.pop(schedule_id, None)
        return True

    def resume_schedule(self, schedule_id: str) -> bool:
        if self.store is None:
            return False

        row = self.store.get(schedule_id)

        if row is None or row["enabled"]:
            return False

        schedule = ScheduleDefinition(
            job_name=row["job_name"],
            frequency=row["frequency"],
            interval_seconds=row["interval_seconds"],
            run_time=(
                time.fromisoformat(row["run_time"])
                if row["run_time"] else None
            ),
            weekdays=tuple(json.loads(row["weekdays_json"])),
            schedule_id=row["schedule_id"],
        )

        self.platform.registry.get(schedule.job_name)

        next_run = datetime.fromisoformat(row["next_run_at"])

        if not self.store.set_enabled(schedule_id, True):
            return False

        self.registry.register(schedule)
        self._next_runs[schedule_id] = next_run
        return True

    def remove_schedule(self, schedule_id: str) -> bool:
        removed = self.registry.remove(schedule_id)
        self._next_runs.pop(schedule_id, None)

        if self.store is not None:
            stored = self.store.remove(schedule_id)
            return removed or stored

        return removed

    def get_next_run(self, schedule_id: str) -> datetime | None:
        return self._next_runs.get(schedule_id)

    def run_due(self, now: datetime | None = None) -> list:
        current_time = now or datetime.now(timezone.utc)
        results = []

        for schedule in self.registry.list_schedules():
            next_run = self._next_runs.get(schedule.schedule_id)

            if next_run is None or current_time < next_run:
                continue

            result = self.platform.run_job(
                name=schedule.job_name,
                trigger="scheduled",
            )
            results.append(result)

            updated_next_run = next_run_time(schedule, current_time)
            self._next_runs[schedule.schedule_id] = updated_next_run

            if self.store is not None:
                self.store.update_next_run(
                    schedule.schedule_id,
                    updated_next_run,
                )

        return results
