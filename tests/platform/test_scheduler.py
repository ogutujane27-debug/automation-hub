import sys
import unittest
from datetime import datetime, time, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from automation_platform.scheduler.models import ScheduleDefinition
from automation_platform.scheduler.registry import ScheduleRegistry
from automation_platform.scheduler.clock import next_run_time


class ScheduleModelTests(unittest.TestCase):

    def test_interval_schedule(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )
        self.assertEqual(schedule.interval_seconds, 300)

    def test_invalid_interval_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="interval",
            )

    def test_daily_schedule(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="daily",
            run_time=time(8, 30),
        )
        self.assertEqual(schedule.run_time, time(8, 30))

    def test_weekly_schedule(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="weekly",
            run_time=time(9, 0),
            weekdays=(0, 4),
        )
        self.assertEqual(schedule.weekdays, (0, 4))



    def test_empty_job_name_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="",
                frequency="interval",
                interval_seconds=60,
            )

    def test_whitespace_job_name_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="   ",
                frequency="interval",
                interval_seconds=60,
            )

    def test_invalid_frequency_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="monthly",
            )

    def test_duplicate_weekdays_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="weekly",
                run_time=time(9, 0),
                weekdays=(0, 0),
            )

    def test_invalid_weekday_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="weekly",
                run_time=time(9, 0),
                weekdays=(7,),
            )

    def test_interval_rejects_run_time(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="interval",
                interval_seconds=60,
                run_time=time(9, 0),
            )

    def test_daily_rejects_interval(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="daily",
                run_time=time(9, 0),
                interval_seconds=60,
            )


    def test_empty_job_name_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="",
                frequency="interval",
                interval_seconds=60,
            )

    def test_whitespace_job_name_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="   ",
                frequency="interval",
                interval_seconds=60,
            )

    def test_invalid_frequency_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="monthly",
            )

    def test_duplicate_weekdays_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="weekly",
                run_time=time(9, 0),
                weekdays=(0, 0),
            )

    def test_invalid_weekday_rejected(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="weekly",
                run_time=time(9, 0),
                weekdays=(7,),
            )

    def test_interval_rejects_run_time(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="interval",
                interval_seconds=60,
                run_time=time(9, 0),
            )

    def test_daily_rejects_interval(self):
        with self.assertRaises(ValueError):
            ScheduleDefinition(
                job_name="platform-test",
                frequency="daily",
                run_time=time(9, 0),
                interval_seconds=60,
            )

class ScheduleRegistryTests(unittest.TestCase):

    def setUp(self):
        self.registry = ScheduleRegistry()
        self.schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="daily",
            run_time=time(8, 30),
        )

    def test_register_and_retrieve(self):
        self.registry.register(self.schedule)
        self.assertEqual(
            self.registry.get(self.schedule.schedule_id),
            self.schedule,
        )

    def test_duplicate_rejected(self):
        self.registry.register(self.schedule)
        with self.assertRaises(ValueError):
            self.registry.register(self.schedule)

    def test_filter_by_job(self):
        self.registry.register(self.schedule)
        self.assertEqual(
            len(self.registry.list_schedules("platform-test")),
            1,
        )

    def test_remove_schedule(self):
        self.registry.register(self.schedule)
        self.assertTrue(self.registry.remove(self.schedule.schedule_id))
        self.assertFalse(self.registry.remove(self.schedule.schedule_id))


class ScheduleClockTests(unittest.TestCase):

    def setUp(self):
        self.after = datetime(
            2026, 11, 16, 8, 0, tzinfo=timezone.utc
        )

    def test_interval_next_run(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )
        self.assertEqual(
            next_run_time(schedule, self.after),
            datetime(2026, 11, 16, 8, 5, tzinfo=timezone.utc),
        )

    def test_daily_next_run(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="daily",
            run_time=time(8, 30),
        )
        self.assertEqual(
            next_run_time(schedule, self.after),
            datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc),
        )

    def test_weekly_next_run(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="weekly",
            run_time=time(9, 0),
            weekdays=(0, 4),
        )
        self.assertEqual(
            next_run_time(schedule, self.after),
            datetime(2026, 11, 16, 9, 0, tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
