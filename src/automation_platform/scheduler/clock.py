"""Calculate the next execution time for a schedule."""

from datetime import datetime, timedelta

from .models import ScheduleDefinition


def next_run_time(
    schedule: ScheduleDefinition,
    after: datetime,
) -> datetime:

    if schedule.frequency == "interval":
        return after + timedelta(
            seconds=schedule.interval_seconds
        )

    if schedule.frequency == "daily":
        candidate = datetime.combine(
            after.date(),
            schedule.run_time,
            tzinfo=after.tzinfo,
        )

        if candidate <= after:
            candidate += timedelta(days=1)

        return candidate

    if schedule.frequency == "weekly":
        for offset in range(8):
            candidate_date = after.date() + timedelta(days=offset)

            if candidate_date.weekday() not in schedule.weekdays:
                continue

            candidate = datetime.combine(
                candidate_date,
                schedule.run_time,
                tzinfo=after.tzinfo,
            )

            if candidate > after:
                return candidate

    raise ValueError("Unable to calculate the next schedule time.")
