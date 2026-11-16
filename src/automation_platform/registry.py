"""Registry for automation jobs."""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class JobDefinition:
    name: str
    description: str
    handler: Callable


class JobRegistry:
    def __init__(self):
        self._jobs: dict[str, JobDefinition] = {}

    def register(self, job: JobDefinition) -> None:
        if not job.name or not job.name.strip():
            raise ValueError("Job name cannot be empty.")

        if job.name in self._jobs:
            raise ValueError(f"Job already registered: {job.name}")

        if not callable(job.handler):
            raise TypeError("Job handler must be callable.")

        self._jobs[job.name] = job

    def get(self, name: str) -> JobDefinition:
        try:
            return self._jobs[name]
        except KeyError:
            raise KeyError(f"Unknown automation job: {name}") from None

    def list_jobs(self) -> list[JobDefinition]:
        return sorted(self._jobs.values(), key=lambda job: job.name)


registry = JobRegistry()
