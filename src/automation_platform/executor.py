"""Execution engine for registered automation jobs."""

from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from .registry import JobDefinition


@dataclass(frozen=True)
class ExecutionContext:
    run_id: str
    job_name: str
    trigger: str
    parameters: dict[str, Any]
    started_at: datetime


@dataclass
class ExecutionResult:
    run_id: str
    job_name: str
    status: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    trigger: str = "manual"
    output: Any = None
    error_type: str | None = None
    error_message: str | None = None


class JobExecutor:

    def execute(
        self,
        job: JobDefinition,
        trigger: str = "manual",
        parameters: dict[str, Any] | None = None,
    ) -> ExecutionResult:

        run_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        timer_start = monotonic()

        context = ExecutionContext(
            run_id=run_id,
            job_name=job.name,
            trigger=trigger,
            parameters=parameters if parameters is not None else {},
            started_at=started_at,
        )

        try:
            output = job.handler(context)

            return ExecutionResult(
                run_id=run_id,
                job_name=job.name,
                status="succeeded",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                duration_seconds=round(monotonic() - timer_start, 6),
                trigger=trigger,
                output=output,
            )

        except Exception as exc:
            return ExecutionResult(
                run_id=run_id,
                job_name=job.name,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                duration_seconds=round(monotonic() - timer_start, 6),
                trigger=trigger,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
