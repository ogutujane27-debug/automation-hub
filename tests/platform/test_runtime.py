import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from automation_platform.runtime import AutomationPlatform
from automation_platform.history.sqlite_store import SQLiteHistoryStore


class AutomationPlatformTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "runtime_test.sqlite3"

        self.platform = AutomationPlatform(
            history_store=SQLiteHistoryStore(database)
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_and_list_jobs(self):
        self.platform.register_job(
            "kubo",
            "Kubo attachment automation",
            lambda context: {"status": "checked"},
        )

        jobs = self.platform.list_jobs()

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].name, "kubo")

    def test_run_registered_job(self):
        self.platform.register_job(
            "auto12",
            "AUTO-12 recurring invoices",
            lambda context: {"message": "test execution"},
        )

        result = self.platform.run_job("auto12")

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.output["message"], "test execution")

    def test_run_is_saved_and_retrievable(self):
        self.platform.register_job(
            "sample",
            "History integration test",
            lambda context: {"message": "saved"},
        )

        result = self.platform.run_job("sample")
        retrieved = self.platform.get_run(result.run_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.run_id, result.run_id)
        self.assertEqual(retrieved.output, {"message": "saved"})

    def test_list_runs_returns_saved_execution(self):
        self.platform.register_job(
            "sample",
            "History listing test",
            lambda context: {"status": "complete"},
        )

        result = self.platform.run_job("sample")
        runs = self.platform.list_runs(job_name="sample")

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].run_id, result.run_id)

    def test_unknown_job_is_rejected(self):
        with self.assertRaises(KeyError):
            self.platform.run_job("unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
