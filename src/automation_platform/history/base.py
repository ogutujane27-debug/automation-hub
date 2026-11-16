"""Execution history storage contract."""

from abc import ABC, abstractmethod

from ..executor import ExecutionResult


class HistoryStore(ABC):

    @abstractmethod
    def save(self, result: ExecutionResult) -> None:
        """Persist an execution result."""
        raise NotImplementedError

    @abstractmethod
    def get(self, run_id: str) -> ExecutionResult | None:
        """Retrieve one execution by its unique ID."""
        raise NotImplementedError

    @abstractmethod
    def list_runs(
        self,
        job_name: str | None = None,
        limit: int = 100,
    ) -> list[ExecutionResult]:
        """List recent executions, optionally filtered by job."""
        raise NotImplementedError
