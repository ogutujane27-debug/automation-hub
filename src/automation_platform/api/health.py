"""HTTP API endpoints for the automation platform."""

import json
from http import HTTPStatus
from urllib.parse import parse_qs, unquote


def create_app(platform):
    """Create a WSGI application using the supplied platform instance."""

    def application(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        if (
            path not in ("/healthz", "/jobs", "/history")
            and not path.startswith("/jobs/")
        ):
            return _respond(
                start_response,
                HTTPStatus.NOT_FOUND,
                {"error": "Not found"},
            )

        if method != "GET":
            return _respond(
                start_response,
                HTTPStatus.METHOD_NOT_ALLOWED,
                {"error": "Method not allowed"},
                extra_headers=[("Allow", "GET")],
            )

        if path == "/healthz":
            return _health_response(platform, start_response)

        if path == "/jobs":
            return _jobs_response(platform, start_response)

        if path == "/history":
            return _history_response(
                platform,
                environ.get("QUERY_STRING", ""),
                start_response,
            )

        job_name = unquote(path[len("/jobs/"):])

        if not job_name or "/" in job_name:
            return _respond(
                start_response,
                HTTPStatus.NOT_FOUND,
                {"error": "Not found"},
            )

        return _job_detail_response(
            platform,
            job_name,
            start_response,
        )

    return application


def _health_response(platform, start_response):
    checks = {
        "runtime": "ok" if platform is not None else "error",
        "history_storage": "error",
        "schedule_storage": "error",
    }

    if platform is not None:
        try:
            platform.history_store.list_runs(limit=1)
            checks["history_storage"] = "ok"
        except Exception:
            checks["history_storage"] = "error"

        try:
            platform.schedule_store.list_schedules()
            checks["schedule_storage"] = "ok"
        except Exception:
            checks["schedule_storage"] = "error"

    healthy = all(value == "ok" for value in checks.values())

    payload = {
        "status": "healthy" if healthy else "degraded",
        "checks": checks,
    }

    status = (
        HTTPStatus.OK
        if healthy
        else HTTPStatus.SERVICE_UNAVAILABLE
    )

    return _respond(start_response, status, payload)


def _jobs_response(platform, start_response):
    if platform is None:
        return _respond(
            start_response,
            HTTPStatus.SERVICE_UNAVAILABLE,
            {"error": "Automation runtime unavailable"},
        )

    try:
        jobs = platform.list_jobs()
    except Exception:
        return _respond(
            start_response,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            {"error": "Unable to retrieve registered automations"},
        )

    payload = {
        "count": len(jobs),
        "jobs": [
            {
                "name": job.name,
                "description": job.description,
            }
            for job in jobs
        ],
    }

    return _respond(start_response, HTTPStatus.OK, payload)


def _job_detail_response(platform, job_name, start_response):
    if platform is None:
        return _respond(
            start_response,
            HTTPStatus.SERVICE_UNAVAILABLE,
            {"error": "Automation runtime unavailable"},
        )

    try:
        job = platform.get_job(job_name)
    except KeyError:
        return _respond(
            start_response,
            HTTPStatus.NOT_FOUND,
            {"error": f"Automation not found: {job_name}"},
        )
    except Exception:
        return _respond(
            start_response,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            {"error": "Unable to retrieve automation details"},
        )

    payload = {
        "name": job.name,
        "description": job.description,
    }

    return _respond(start_response, HTTPStatus.OK, payload)


def _history_response(platform, query_string, start_response):
    if platform is None:
        return _respond(
            start_response,
            HTTPStatus.SERVICE_UNAVAILABLE,
            {"error": "Automation runtime unavailable"},
        )

    query = parse_qs(query_string, keep_blank_values=True)

    if any(len(values) != 1 for values in query.values()):
        return _respond(
            start_response,
            HTTPStatus.BAD_REQUEST,
            {"error": "Each query parameter must be supplied once"},
        )

    unsupported = set(query) - {"limit", "job_name"}

    if unsupported:
        return _respond(
            start_response,
            HTTPStatus.BAD_REQUEST,
            {"error": "Unsupported query parameter"},
        )

    raw_limit = query.get("limit", ["100"])[0]

    try:
        limit = int(raw_limit)
    except ValueError:
        return _respond(
            start_response,
            HTTPStatus.BAD_REQUEST,
            {"error": "Limit must be a positive integer no greater than 500"},
        )

    if not 1 <= limit <= 500:
        return _respond(
            start_response,
            HTTPStatus.BAD_REQUEST,
            {"error": "Limit must be between 1 and 500"},
        )

    job_name = query.get("job_name", [None])[0]

    if job_name is not None:
        job_name = job_name.strip()

        if not job_name:
            return _respond(
                start_response,
                HTTPStatus.BAD_REQUEST,
                {"error": "Job name cannot be empty"},
            )

    try:
        runs = platform.list_runs(
            job_name=job_name,
            limit=limit,
        )
    except Exception:
        return _respond(
            start_response,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            {"error": "Unable to retrieve execution history"},
        )

    payload = {
        "count": len(runs),
        "runs": [
            {
                "run_id": run.run_id,
                "job_name": run.job_name,
                "status": run.status,
                "trigger": run.trigger,
                "started_at": run.started_at.isoformat(),
                "finished_at": run.finished_at.isoformat(),
                "duration_seconds": run.duration_seconds,
                "output": run.output,
                "error_type": run.error_type,
                "error_message": run.error_message,
            }
            for run in runs
        ],
    }

    return _respond(start_response, HTTPStatus.OK, payload)


def _respond(start_response, status, payload, extra_headers=None):
    body = json.dumps(payload, default=str).encode("utf-8")

    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]

    if extra_headers:
        headers.extend(extra_headers)

    start_response(
        f"{status.value} {status.phrase}",
        headers,
    )

    return [body]
