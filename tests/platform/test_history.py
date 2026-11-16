import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.automation_platform.executor import ExecutionResult
from src.automation_platform.history.sqlite_store import SQLiteHistoryStore


class SQLiteHistoryStoreTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "history.sqlite3"
        self.store = SQLiteHistoryStore(self.database)

        now = datetime.now(timezone.utc)
        self.result = ExecutionResult(
            run_id="test-run-001",
            job_name="sample-job",
            status="succeeded",
            started_at=now,
            finished_at=now,
            duration_seconds=0.25,
            output={"message": "completed"},
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_retrieve(self):
        self.store.save(self.result)
        retrieved = self.store.get("test-run-001")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.job_name, "sample-job")
        self.assertEqual(retrieved.output, {"message": "completed"})
        self.assertEqual(retrieved.trigger, "manual")

    def test_trigger_is_saved_and_retrieved(self):
        scheduled_result = ExecutionResult(
            run_id="scheduled-run-001",
            job_name="sample-job",
            status="succeeded",
            started_at=self.result.started_at,
            finished_at=self.result.finished_at,
            duration_seconds=0.25,
            trigger="scheduled",
            output={"message": "scheduled execution"},
        )

        self.store.save(scheduled_result)
        retrieved = self.store.get("scheduled-run-001")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.trigger, "scheduled")

    def test_legacy_database_migration_preserves_records(self):
        legacy_database = Path(self.temp_dir.name) / "legacy.sqlite3"
        connection = sqlite3.connect(legacy_database)
        connection.execute("""
            CREATE TABLE execution_history (
                run_id TEXT PRIMARY KEY,
                job_name TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                output_json TEXT,
                error_type TEXT,
                error_message TEXT
            )
        """)

        now = datetime.now(timezone.utc).isoformat()

        connection.execute("""
            INSERT INTO execution_history (
                run_id, job_name, status, started_at, finished_at,
                duration_seconds, output_json, error_type, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "legacy-run-001",
            "old-job",
            "succeeded",
            now,
            now,
            0.5,
            '{"message": "old record"}',
            None,
            None,
        ))

        connection.commit()
        connection.close()

        migrated_store = SQLiteHistoryStore(legacy_database)
        retrieved = migrated_store.get("legacy-run-001")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.job_name, "old-job")
        self.assertEqual(retrieved.output, {"message": "old record"})
        self.assertEqual(retrieved.trigger, "manual")

    def test_list_runs(self):
        self.store.save(self.result)

        runs = self.store.list_runs()

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].run_id, "test-run-001")

    def test_filter_by_job_name(self):
        self.store.save(self.result)

        self.assertEqual(len(self.store.list_runs("sample-job")), 1)
        self.assertEqual(len(self.store.list_runs("another-job")), 0)

    def test_reject_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.store.list_runs(limit=0)


if __name__ == "__main__":
    unittest.main()
