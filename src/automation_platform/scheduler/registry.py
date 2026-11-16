"""Registry for automation schedules."""

from .models import ScheduleDefinition


class ScheduleRegistry:

    def __init__(self):
        self._schedules: dict[str, ScheduleDefinition] = {}

    def register(self, schedule: ScheduleDefinition) -> None:
        if schedule.schedule_id in self._schedules:
            raise ValueError(
                f"Schedule already registered: {schedule.schedule_id}"
            )

        self._schedules[schedule.schedule_id] = schedule

    def get(self, schedule_id: str) -> ScheduleDefinition:
        try:
            return self._schedules[schedule_id]
        except KeyError:
            raise KeyError(
                f"Unknown schedule: {schedule_id}"
            ) from None

    def list_schedules(
        self,
        job_name: str | None = None,
    ) -> list[ScheduleDefinition]:
        schedules = list(self._schedules.values())

        if job_name:
            schedules = [
                schedule
                for schedule in schedules
                if schedule.job_name == job_name
            ]

        return sorted(
            schedules,
            key=lambda schedule: schedule.schedule_id,
        )

    def remove(self, schedule_id: str) -> bool:
        return self._schedules.pop(schedule_id, None) is not None
