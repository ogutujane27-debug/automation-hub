"""Central interface for registering and executing automations."""

from pathlib import Path
from typing import Any, Callable

from .registry import JobDefinition, JobRegistry
from .executor import ExecutionResult, JobExecutor
from .history.base import HistoryStore
from .history.sqlite_store import SQLiteHistoryStore
from .scheduler.sqlite_store import SQLiteScheduleStore


class AutomationPlatform:

    def __init__(
        self,
        history_store: HistoryStore | None = None,
    ):
        self.registry = JobRegistry()
        self.executor = JobExecutor()

        self.history_store = (
            history_store
            if history_store is not None
            else SQLiteHistoryStore(
                Path("data/automation_platform/history.sqlite3")
            )
        )

        database_path = getattr(
            self.history_store,
            "database_path",
            Path("data/automation_platform/schedules.sqlite3"),
        )

        self.schedule_store = SQLiteScheduleStore(database_path)

    def register_job(
        self,
        name: str,
        description: str,
        handler: Callable,
    ) -> None:
        job = JobDefinition(
            name=name,
            description=description,
            handler=handler,
        )
        self.registry.register(job)

    def list_jobs(self) -> list[JobDefinition]:
        return self.registry.list_jobs()

    def run_job(
        self,
        name: str,
        trigger: str = "manual",
        parameters: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        job = self.registry.get(name)

        result = self.executor.execute(
            job=job,
            trigger=trigger,
            parameters=parameters,
        )

        self.history_store.save(result)

        return result

    def get_run(self, run_id: str) -> ExecutionResult | None:
        return self.history_store.get(run_id)

    def list_runs(
        self,
        job_name: str | None = None,
        limit: int = 100,
    ) -> list[ExecutionResult]:
        return self.history_store.list_runs(
            job_name=job_name,
            limit=limit,
        )
