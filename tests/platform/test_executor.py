import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from automation_platform.registry import JobDefinition
from automation_platform.executor import JobExecutor


class JobExecutorTests(unittest.TestCase):

    def setUp(self):
        self.executor = JobExecutor()

    def test_successful_execution(self):
        job = JobDefinition(
            "test-job",
            "Test successful execution",
            lambda context: {"message": "completed"},
        )

        result = self.executor.execute(job)

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.output["message"], "completed")
        self.assertIsNone(result.error_message)
        self.assertTrue(result.run_id)

    def test_failed_execution(self):
        def failing_handler(context):
            raise RuntimeError("Test failure")

        job = JobDefinition(
            "failing-job",
            "Test failed execution",
            failing_handler,
        )

        result = self.executor.execute(job)

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_type, "RuntimeError")
        self.assertEqual(result.error_message, "Test failure")

    def test_execution_context(self):
        def handler(context):
            return {
                "job": context.job_name,
                "trigger": context.trigger,
                "parameters": context.parameters,
            }

        job = JobDefinition("context-job", "Context test", handler)

        result = self.executor.execute(
            job,
            trigger="manual",
            parameters={"environment": "development"},
        )

        self.assertEqual(result.output["job"], "context-job")
        self.assertEqual(result.output["trigger"], "manual")
        self.assertEqual(
            result.output["parameters"]["environment"],
            "development",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
