import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from src.automation_platform.api import create_app


class FakeHistoryStore:

    def __init__(self, should_fail=False, runs=None):
        self.should_fail = should_fail
        self.runs = runs or []

    def list_runs(self, job_name=None, limit=100):
        if self.should_fail:
            raise RuntimeError("History database unavailable")

        runs = self.runs

        if job_name is not None:
            runs = [
                run for run in runs
                if run.job_name == job_name
            ]

        return runs[:limit]


class FakeScheduleStore:

    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def list_schedules(self):
        if self.should_fail:
            raise RuntimeError("Schedule database unavailable")
        return []


class FakePlatform:

    def __init__(
        self,
        history_failure=False,
        schedule_failure=False,
        jobs=None,
        jobs_failure=False,
        job_failure=False,
        history_runs=None,
    ):
        self.history_store = FakeHistoryStore(history_failure, history_runs)
        self.schedule_store = FakeScheduleStore(schedule_failure)
        self.jobs = jobs or []
        self.jobs_failure = jobs_failure
        self.job_failure = job_failure

    def list_jobs(self):
        if self.jobs_failure:
            raise RuntimeError("Registry unavailable")
        return self.jobs

    def get_job(self, name):
        if self.job_failure:
            raise RuntimeError("Registry unavailable")

        for job in self.jobs:
            if job.name == name:
                return job

        raise KeyError(f"Unknown automation job: {name}")

    def list_runs(self, job_name=None, limit=100):
        return self.history_store.list_runs(
            job_name=job_name,
            limit=limit,
        )


class APIEndpointTests(unittest.TestCase):

    def call_app(self, app, method="GET", path="/healthz", query_string=""):
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
        }

        body = b"".join(app(environ, start_response))

        captured["body"] = json.loads(body.decode("utf-8"))
        return captured


class HealthEndpointTests(APIEndpointTests):

    def test_healthcheck_returns_200_when_all_checks_pass(self):
        app = create_app(FakePlatform())
        response = self.call_app(app)

        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(response["body"]["status"], "healthy")
        self.assertEqual(
            response["body"]["checks"],
            {
                "runtime": "ok",
                "history_storage": "ok",
                "schedule_storage": "ok",
            },
        )

    def test_healthcheck_returns_503_when_history_storage_fails(self):
        app = create_app(FakePlatform(history_failure=True))
        response = self.call_app(app)

        self.assertTrue(response["status"].startswith("503"))
        self.assertEqual(response["body"]["status"], "degraded")
        self.assertEqual(
            response["body"]["checks"]["history_storage"],
            "error",
        )

    def test_healthcheck_returns_503_when_schedule_storage_fails(self):
        app = create_app(FakePlatform(schedule_failure=True))
        response = self.call_app(app)

        self.assertTrue(response["status"].startswith("503"))
        self.assertEqual(response["body"]["status"], "degraded")
        self.assertEqual(
            response["body"]["checks"]["schedule_storage"],
            "error",
        )

    def test_unknown_path_returns_404(self):
        app = create_app(FakePlatform())
        response = self.call_app(app, path="/unknown")

        self.assertTrue(response["status"].startswith("404"))

    def test_non_get_method_returns_405(self):
        app = create_app(FakePlatform())
        response = self.call_app(app, method="POST")

        self.assertTrue(response["status"].startswith("405"))
        self.assertEqual(response["headers"]["Allow"], "GET")


class JobsEndpointTests(APIEndpointTests):

    def test_jobs_returns_registered_jobs(self):
        jobs = [
            SimpleNamespace(
                name="invoice-automation",
                description="Process recurring invoices",
                handler=lambda: None,
            ),
            SimpleNamespace(
                name="sales-report",
                description="Generate sales reports",
                handler=lambda: None,
            ),
        ]
        app = create_app(FakePlatform(jobs=jobs))
        response = self.call_app(app, path="/jobs")

        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(response["body"]["count"], 2)
        self.assertEqual(
            response["body"]["jobs"],
            [
                {
                    "name": "invoice-automation",
                    "description": "Process recurring invoices",
                },
                {
                    "name": "sales-report",
                    "description": "Generate sales reports",
                },
            ],
        )
        self.assertNotIn("handler", response["body"]["jobs"][0])

    def test_jobs_returns_empty_list_when_no_jobs_registered(self):
        app = create_app(FakePlatform())
        response = self.call_app(app, path="/jobs")

        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(response["body"], {"count": 0, "jobs": []})

    def test_jobs_rejects_non_get_method(self):
        app = create_app(FakePlatform())
        response = self.call_app(app, method="POST", path="/jobs")

        self.assertTrue(response["status"].startswith("405"))
        self.assertEqual(response["headers"]["Allow"], "GET")

    def test_jobs_returns_500_when_registry_fails(self):
        app = create_app(FakePlatform(jobs_failure=True))
        response = self.call_app(app, path="/jobs")

        self.assertTrue(response["status"].startswith("500"))
        self.assertEqual(
            response["body"]["error"],
            "Unable to retrieve registered automations",
        )


class JobDetailEndpointTests(APIEndpointTests):

    def setUp(self):
        self.jobs = [
            SimpleNamespace(
                name="invoice-automation",
                description="Process recurring invoices",
                handler=lambda: None,
            )
        ]

    def test_job_detail_returns_registered_job(self):
        app = create_app(FakePlatform(jobs=self.jobs))
        response = self.call_app(
            app,
            path="/jobs/invoice-automation",
        )

        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(
            response["body"],
            {
                "name": "invoice-automation",
                "description": "Process recurring invoices",
            },
        )
        self.assertNotIn("handler", response["body"])

    def test_job_detail_returns_404_for_unknown_job(self):
        app = create_app(FakePlatform(jobs=self.jobs))
        response = self.call_app(
            app,
            path="/jobs/unknown-job",
        )

        self.assertTrue(response["status"].startswith("404"))
        self.assertEqual(
            response["body"]["error"],
            "Automation not found: unknown-job",
        )

    def test_job_detail_returns_500_when_registry_fails(self):
        app = create_app(
            FakePlatform(jobs=self.jobs, job_failure=True)
        )
        response = self.call_app(
            app,
            path="/jobs/invoice-automation",
        )

        self.assertTrue(response["status"].startswith("500"))
        self.assertEqual(
            response["body"]["error"],
            "Unable to retrieve automation details",
        )

    def test_job_detail_rejects_non_get_method(self):
        app = create_app(FakePlatform(jobs=self.jobs))
        response = self.call_app(
            app,
            method="POST",
            path="/jobs/invoice-automation",
        )

        self.assertTrue(response["status"].startswith("405"))
        self.assertEqual(response["headers"]["Allow"], "GET")

    def test_job_detail_rejects_empty_name(self):
        app = create_app(FakePlatform())
        response = self.call_app(app, path="/jobs/")

        self.assertTrue(response["status"].startswith("404"))


if __name__ == "__main__":
    unittest.main()



class HistoryEndpointTests(APIEndpointTests):

    def setUp(self):
        now = datetime.now(timezone.utc)

        self.runs = [
            SimpleNamespace(
                run_id="run-001",
                job_name="platform-test",
                status="succeeded",
                trigger="manual",
                started_at=now,
                finished_at=now,
                duration_seconds=0.25,
                output={"message": "completed"},
                error_type=None,
                error_message=None,
            ),
            SimpleNamespace(
                run_id="run-002",
                job_name="invoice-automation",
                status="failed",
                trigger="scheduled",
                started_at=now,
                finished_at=now,
                duration_seconds=0.5,
                output=None,
                error_type="RuntimeError",
                error_message="Invoice source unavailable",
            ),
        ]

    def test_history_returns_execution_records(self):
        app = create_app(FakePlatform(history_runs=self.runs))
        response = self.call_app(app, path="/history")

        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(response["body"]["count"], 2)

        first_run = response["body"]["runs"][0]
        self.assertEqual(first_run["run_id"], "run-001")
        self.assertEqual(first_run["job_name"], "platform-test")
        self.assertEqual(first_run["status"], "succeeded")
        self.assertEqual(first_run["trigger"], "manual")
        self.assertEqual(first_run["duration_seconds"], 0.25)
        self.assertEqual(first_run["output"], {"message": "completed"})
        self.assertIsNone(first_run["error_type"])
        self.assertIsNone(first_run["error_message"])
        self.assertIn("T", first_run["started_at"])
        self.assertIn("T", first_run["finished_at"])

    def test_history_returns_empty_list(self):
        app = create_app(FakePlatform())
        response = self.call_app(app, path="/history")

        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(response["body"], {"count": 0, "runs": []})

    def test_history_filters_by_job_name(self):
        app = create_app(FakePlatform(history_runs=self.runs))
        response = self.call_app(
            app,
            path="/history",
            query_string="job_name=platform-test",
        )

        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(response["body"]["count"], 1)
        self.assertEqual(
            response["body"]["runs"][0]["job_name"],
            "platform-test",
        )

    def test_history_respects_limit(self):
        app = create_app(FakePlatform(history_runs=self.runs))
        response = self.call_app(
            app,
            path="/history",
            query_string="limit=1",
        )

        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(response["body"]["count"], 1)

    def test_history_rejects_invalid_limit(self):
        for limit in ("abc", "0", "-1"):
            with self.subTest(limit=limit):
                app = create_app(FakePlatform())
                response = self.call_app(
                    app,
                    path="/history",
                    query_string=f"limit={limit}",
                )
                self.assertTrue(response["status"].startswith("400"))

    def test_history_rejects_limit_above_maximum(self):
        app = create_app(FakePlatform())
        response = self.call_app(
            app,
            path="/history",
            query_string="limit=501",
        )

        self.assertTrue(response["status"].startswith("400"))

    def test_history_rejects_empty_job_name(self):
        app = create_app(FakePlatform())
        response = self.call_app(
            app,
            path="/history",
            query_string="job_name=",
        )

        self.assertTrue(response["status"].startswith("400"))

    def test_history_returns_500_when_storage_fails(self):
        app = create_app(FakePlatform(history_failure=True))
        response = self.call_app(app, path="/history")

        self.assertTrue(response["status"].startswith("500"))
        self.assertEqual(
            response["body"]["error"],
            "Unable to retrieve execution history",
        )

    def test_history_rejects_non_get_method(self):
        app = create_app(FakePlatform())
        response = self.call_app(
            app,
            method="POST",
            path="/history",
        )

        self.assertTrue(response["status"].startswith("405"))
        self.assertEqual(response["headers"]["Allow"], "GET")
