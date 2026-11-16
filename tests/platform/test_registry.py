import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from automation_platform.registry import JobDefinition, JobRegistry


class JobRegistryTests(unittest.TestCase):

    def setUp(self):
        self.registry = JobRegistry()
        self.handler = lambda: {"status": "success"}

    def test_register_and_retrieve_job(self):
        job = JobDefinition("kubo", "Kubo attachment automation", self.handler)
        self.registry.register(job)
        self.assertEqual(self.registry.get("kubo"), job)

    def test_list_jobs_alphabetically(self):
        self.registry.register(JobDefinition("zeta", "Second", self.handler))
        self.registry.register(JobDefinition("alpha", "First", self.handler))
        self.assertEqual(
            [job.name for job in self.registry.list_jobs()],
            ["alpha", "zeta"],
        )

    def test_reject_duplicate_names(self):
        job = JobDefinition("kubo", "Kubo automation", self.handler)
        self.registry.register(job)
        with self.assertRaises(ValueError):
            self.registry.register(job)

    def test_reject_empty_name(self):
        job = JobDefinition("", "Invalid job", self.handler)
        with self.assertRaises(ValueError):
            self.registry.register(job)

    def test_reject_non_callable_handler(self):
        job = JobDefinition("invalid", "Invalid handler", None)
        with self.assertRaises(TypeError):
            self.registry.register(job)


if __name__ == "__main__":
    unittest.main(verbosity=2)
