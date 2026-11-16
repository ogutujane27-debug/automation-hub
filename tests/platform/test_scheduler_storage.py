import sys
import tempfile
import unittest
from datetime import datetime, time, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from automation_platform.scheduler.models import ScheduleDefinition
from automation_platform.scheduler.sqlite_store import SQLiteScheduleStore


class SQLiteScheduleStoreTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "schedules.sqlite3"
        self.store = SQLiteScheduleStore(database)

        self.schedule = ScheduleDefinition(
            job_name="platform-test",
            frequency="weekly",
            run_time=time(9, 0),
            weekdays=(0, 4),
        )

        self.next_run = datetime(
            2026, 11, 16, 9, 0, tzinfo=timezone.utc
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_retrieve(self):
        self.store.save(self.schedule, self.next_run)

        record = self.store.get(self.schedule.schedule_id)

        self.assertEqual(record["job_name"], "platform-test")
        self.assertEqual(record["frequency"], "weekly")
        self.assertEqual(record["enabled"], 1)

    def test_list_schedules(self):
        self.store.save(self.schedule, self.next_run)

        records = self.store.list_schedules()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["schedule_id"], self.schedule.schedule_id)

    def test_disable_and_enable(self):
        self.store.save(self.schedule, self.next_run)

        self.assertTrue(
            self.store.set_enabled(self.schedule.schedule_id, False)
        )
        self.assertEqual(self.store.list_schedules(enabled_only=True), [])

        self.assertTrue(
            self.store.set_enabled(self.schedule.schedule_id, True)
        )
        self.assertEqual(len(self.store.list_schedules(enabled_only=True)), 1)

    def test_update_next_run(self):
        self.store.save(self.schedule, self.next_run)

        updated = datetime(
            2026, 11, 20, 9, 0, tzinfo=timezone.utc
        )

        self.store.update_next_run(self.schedule.schedule_id, updated)

        record = self.store.get(self.schedule.schedule_id)
        self.assertEqual(
            datetime.fromisoformat(record["next_run_at"]),
            updated,
        )

    def test_remove_schedule(self):
        self.store.save(self.schedule, self.next_run)

        self.assertTrue(self.store.remove(self.schedule.schedule_id))
        self.assertFalse(self.store.remove(self.schedule.schedule_id))
        self.assertIsNone(self.store.get(self.schedule.schedule_id))


if __name__ == "__main__":
    unittest.main(verbosity=2)
