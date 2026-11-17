import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from automation_platform.runtime import AutomationPlatform
from automation_platform.history.sqlite_store import SQLiteHistoryStore
from automation_platform.scheduler.engine import SchedulerEngine
from automation_platform.scheduler.models import ScheduleDefinition
from automation_platform.cli import __main__ as cli


class ScheduleCliTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "cli_test.sqlite3"

        self.platform = AutomationPlatform(
            history_store=SQLiteHistoryStore(database)
        )

        self.platform.register_job(
            "platform-test",
            "Safe CLI test automation",
            lambda context: {"message": "CLI test"},
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch.object(
                cli, "AutomationPlatform",
                return_value=self.platform,
            ),
            patch.object(
                cli, "load_jobs",
                side_effect=lambda platform: platform,
            ),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            result = cli.main(arguments)

        return result, stdout.getvalue(), stderr.getvalue()

    def test_add_interval_schedule(self):
        result, output, error = self.run_cli([
            "schedule", "add", "platform-test",
            "--frequency", "interval",
            "--interval-seconds", "300",
        ])

        self.assertEqual(result, 0)
        self.assertIn("Schedule created:", output)
        self.assertEqual(error, "")
        self.assertEqual(len(self.platform.schedule_store.list_schedules()), 1)

    def test_add_daily_schedule(self):
        result, output, error = self.run_cli([
            "schedule", "add", "platform-test",
            "--frequency", "daily",
            "--run-time", "08:30",
        ])

        self.assertEqual(result, 0)
        self.assertIn("Schedule created:", output)
        self.assertEqual(error, "")

    def test_add_weekly_schedule(self):
        result, output, error = self.run_cli([
            "schedule", "add", "platform-test",
            "--frequency", "weekly",
            "--run-time", "09:00",
            "--weekdays", "monday,friday",
        ])

        self.assertEqual(result, 0)
        self.assertIn("Schedule created:", output)
        self.assertEqual(error, "")

    def test_reject_non_positive_interval(self):
        result, output, error = self.run_cli([
            "schedule", "add", "platform-test",
            "--frequency", "interval",
            "--interval-seconds", "0",
        ])

        self.assertEqual(result, 1)
        self.assertIn("Unable to add schedule:", error)
        self.assertEqual(self.platform.schedule_store.list_schedules(), [])

    def test_reject_daily_schedule_without_run_time(self):
        result, output, error = self.run_cli([
            "schedule", "add", "platform-test",
            "--frequency", "daily",
        ])

        self.assertEqual(result, 1)
        self.assertIn("Daily schedules require --run-time", error)

    def test_reject_invalid_weekday(self):
        result, output, error = self.run_cli([
            "schedule", "add", "platform-test",
            "--frequency", "weekly",
            "--run-time", "09:00",
            "--weekdays", "monday,funday",
        ])

        self.assertEqual(result, 1)
        self.assertIn("Invalid weekday", error)

    def test_reject_duplicate_weekdays(self):
        result, output, error = self.run_cli([
            "schedule", "add", "platform-test",
            "--frequency", "weekly",
            "--run-time", "09:00",
            "--weekdays", "monday,monday",
        ])

        self.assertEqual(result, 1)
        self.assertIn("must not contain duplicates", error)

    def test_reject_unknown_job(self):
        result, output, error = self.run_cli([
            "schedule", "add", "unknown-job",
            "--frequency", "interval",
            "--interval-seconds", "300",
        ])

        self.assertEqual(result, 1)
        self.assertIn("Unable to add schedule:", error)

    def test_list_empty_schedules(self):
        result, output, error = self.run_cli([
            "schedule", "list",
        ])

        self.assertEqual(result, 0)
        self.assertIn("No schedules found.", output)
        self.assertEqual(error, "")

    def test_list_filters_by_job(self):
        engine = SchedulerEngine(self.platform)

        engine.add_schedule(ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        ))

        result, output, error = self.run_cli([
            "schedule", "list", "--job", "unknown-job",
        ])

        self.assertEqual(result, 0)
        self.assertIn("No schedules found.", output)

    def test_pause_resume_and_remove_schedule(self):
        engine = SchedulerEngine(self.platform)
        schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="interval",
            interval_seconds=300,
        )
        engine.add_schedule(schedule)

        result, output, error = self.run_cli([
            "schedule", "pause", schedule.schedule_id,
        ])
        self.assertEqual(result, 0)
        self.assertIn("Schedule paused:", output)

        result, output, error = self.run_cli([
            "schedule", "list",
        ])
        self.assertEqual(result, 0)
        self.assertIn("paused", output)

        result, output, error = self.run_cli([
            "schedule", "resume", schedule.schedule_id,
        ])
        self.assertEqual(result, 0)
        self.assertIn("Schedule resumed:", output)

        result, output, error = self.run_cli([
            "schedule", "remove", schedule.schedule_id,
        ])
        self.assertEqual(result, 0)
        self.assertIn("Schedule removed:", output)

        self.assertEqual(self.platform.schedule_store.list_schedules(), [])

    def test_unknown_schedule_operations_return_errors(self):
        for action in ("pause", "resume", "remove"):
            with self.subTest(action=action):
                result, output, error = self.run_cli([
                    "schedule", action, "unknown-schedule-id",
                ])

                self.assertEqual(result, 1)
                self.assertNotEqual(error, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
