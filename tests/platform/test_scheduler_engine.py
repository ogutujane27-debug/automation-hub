import sys
import tempfile
import unittest
from datetime import datetime, time, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from automation_platform.runtime import AutomationPlatform
from automation_platform.history.sqlite_store import SQLiteHistoryStore
from automation_platform.scheduler.models import ScheduleDefinition
from automation_platform.scheduler.engine import SchedulerEngine


class SchedulerEngineTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "scheduler_test.sqlite3"

        self.platform = AutomationPlatform(
            history_store=SQLiteHistoryStore(database)
        )

        self.platform.register_job(
            "platform-test",
            "Safe scheduler engine test",
            lambda context: {"message": "scheduled execution"},
        )

        self.engine = SchedulerEngine(self.platform)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_schedule(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="daily",
            run_time=time(8, 30),
        )

        self.engine.add_schedule(schedule)

        self.assertEqual(
            self.engine.registry.get(schedule.schedule_id),
            schedule,
        )
        self.assertIsNotNone(
            self.engine.get_next_run(schedule.schedule_id)
        )

    def test_unknown_job_rejected(self):
        schedule = ScheduleDefinition(
            job_name="unknown",
            frequency="daily",
            run_time=time(8, 30),
        )

        with self.assertRaises(KeyError):
            self.engine.add_schedule(schedule)

    def test_job_not_run_before_due_time(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )

        self.engine.add_schedule(schedule)

        results = self.engine.run_due(
            datetime(2026, 11, 16, 7, 0, tzinfo=timezone.utc)
        )

        self.assertEqual(results, [])
        self.assertEqual(self.platform.list_runs(), [])

    def test_due_job_executes_and_is_saved(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )

        self.engine.add_schedule(schedule)

        due_time = self.engine.get_next_run(schedule.schedule_id)
        results = self.engine.run_due(due_time)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "succeeded")
        self.assertEqual(results[0].trigger, "scheduled")

        history = self.platform.list_runs(job_name="platform-test")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].run_id, results[0].run_id)

    def test_remove_schedule(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="daily",
            run_time=time(8, 30),
        )

        self.engine.add_schedule(schedule)

        self.assertTrue(
            self.engine.remove_schedule(schedule.schedule_id)
        )
        self.assertFalse(
            self.engine.remove_schedule(schedule.schedule_id)
        )
        self.assertIsNone(
            self.engine.get_next_run(schedule.schedule_id)
        )


    def test_same_due_time_does_not_execute_twice(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )

        self.engine.add_schedule(schedule)

        due_time = self.engine.get_next_run(schedule.schedule_id)

        first_results = self.engine.run_due(due_time)
        second_results = self.engine.run_due(due_time)

        self.assertEqual(len(first_results), 1)
        self.assertEqual(second_results, [])
        self.assertEqual(len(self.platform.list_runs()), 1)




    def test_schedule_survives_engine_restart(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )

        self.engine.add_schedule(schedule)
        saved_next_run = self.engine.get_next_run(schedule.schedule_id)

        restarted_engine = SchedulerEngine(self.platform)

        self.assertEqual(
            restarted_engine.registry.get(schedule.schedule_id),
            schedule,
        )
        self.assertEqual(
            restarted_engine.get_next_run(schedule.schedule_id),
            saved_next_run,
        )

    def test_updated_next_run_survives_engine_restart(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )

        self.engine.add_schedule(schedule)
        due_time = self.engine.get_next_run(schedule.schedule_id)

        self.engine.run_due(due_time)
        updated_next_run = self.engine.get_next_run(schedule.schedule_id)

        restarted_engine = SchedulerEngine(self.platform)

        self.assertEqual(
            restarted_engine.get_next_run(schedule.schedule_id),
            updated_next_run,
        )

    def test_pause_schedule(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )

        self.engine.add_schedule(schedule)
        self.assertTrue(self.engine.pause_schedule(schedule.schedule_id))

        stored = self.platform.schedule_store.get(schedule.schedule_id)

        self.assertEqual(stored["enabled"], 0)
        self.assertIsNone(self.engine.get_next_run(schedule.schedule_id))
        self.assertEqual(self.engine.list_schedules(), [])

    def test_resume_schedule_preserves_next_run(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )

        self.engine.add_schedule(schedule)
        original_next_run = self.engine.get_next_run(schedule.schedule_id)

        self.engine.pause_schedule(schedule.schedule_id)
        self.assertTrue(self.engine.resume_schedule(schedule.schedule_id))

        self.assertEqual(
            self.engine.get_next_run(schedule.schedule_id),
            original_next_run,
        )
        self.assertEqual(
            self.engine.registry.get(schedule.schedule_id),
            schedule,
        )

    def test_paused_schedule_is_not_loaded_after_restart(self):
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )

        self.engine.add_schedule(schedule)
        self.engine.pause_schedule(schedule.schedule_id)

        restarted_engine = SchedulerEngine(self.platform)

        self.assertEqual(restarted_engine.list_schedules(), [])
        self.assertIsNone(
            restarted_engine.get_next_run(schedule.schedule_id)
        )

    def test_pause_unknown_schedule_returns_false(self):
        self.assertFalse(
            self.engine.pause_schedule("unknown-schedule-id")
        )
if __name__ == "__main__":
    unittest.main(verbosity=2)
