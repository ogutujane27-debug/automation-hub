"""Definitions and validation for automation schedules."""

from dataclasses import dataclass
from datetime import time
from uuid import uuid4


@dataclass(frozen=True)
class ScheduleDefinition:
    job_name: str
    frequency: str
    interval_seconds: int | None = None
    run_time: time | None = None
    weekdays: tuple[int, ...] = ()
    schedule_id: str = ""

    def __post_init__(self):
        if not isinstance(self.job_name, str) or not self.job_name.strip():
            raise ValueError("Job name must be a non-empty string.")

        if self.frequency not in {"interval", "daily", "weekly"}:
            raise ValueError("Frequency must be interval, daily, or weekly.")

        if not isinstance(self.weekdays, tuple):
            raise ValueError("Weekdays must be supplied as a tuple.")

        if self.frequency == "interval":
            if (
                isinstance(self.interval_seconds, bool)
                or not isinstance(self.interval_seconds, int)
                or self.interval_seconds < 1
            ):
                raise ValueError(
                    "Interval schedules require positive integer interval_seconds."
                )

            if self.run_time is not None or self.weekdays:
                raise ValueError(
                    "Interval schedules cannot have run_time or weekdays."
                )

        elif self.frequency == "daily":
            if not isinstance(self.run_time, time):
                raise ValueError("Daily schedules require a valid run_time.")

            if self.interval_seconds is not None or self.weekdays:
                raise ValueError(
                    "Daily schedules cannot have interval_seconds or weekdays."
                )

        elif self.frequency == "weekly":
            if not isinstance(self.run_time, time):
                raise ValueError("Weekly schedules require a valid run_time.")

            if self.interval_seconds is not None:
                raise ValueError(
                    "Weekly schedules cannot have interval_seconds."
                )

            if not self.weekdays:
                raise ValueError("Weekly schedules require at least one weekday.")

            if any(
                isinstance(day, bool)
                or not isinstance(day, int)
                or day < 0
                or day > 6
                for day in self.weekdays
            ):
                raise ValueError(
                    "Weekdays must be integers between 0 (Monday) and 6 (Sunday)."
                )

            if len(set(self.weekdays)) != len(self.weekdays):
                raise ValueError("Weekly schedules cannot contain duplicate weekdays.")

        if not self.schedule_id:
            object.__setattr__(self, "schedule_id", str(uuid4()))
