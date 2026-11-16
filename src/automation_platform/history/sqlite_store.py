"""SQLite implementation of the execution history store."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from ..executor import ExecutionResult
from .base import HistoryStore


class SQLiteHistoryStore(HistoryStore):

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
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

            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(execution_history)"
                ).fetchall()
            }

            if "trigger" not in columns:
                connection.execute("""
                    ALTER TABLE execution_history
                    ADD COLUMN trigger TEXT NOT NULL DEFAULT 'manual'
                """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_execution_history_job
                ON execution_history(job_name)
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_execution_history_started
                ON execution_history(started_at)
            """)

    @staticmethod
    def _serialize_output(output: Any) -> str | None:
        if output is None:
            return None
        try:
            return json.dumps(output, default=str)
        except (TypeError, ValueError):
            return json.dumps(str(output))

    @staticmethod
    def _to_result(row: sqlite3.Row) -> ExecutionResult:
        output = (
            json.loads(row["output_json"])
            if row["output_json"] is not None
            else None
        )

        return ExecutionResult(
            run_id=row["run_id"],
            job_name=row["job_name"],
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=datetime.fromisoformat(row["finished_at"]),
            duration_seconds=row["duration_seconds"],
            trigger=row["trigger"],
            output=output,
            error_type=row["error_type"],
            error_message=row["error_message"],
        )

    def save(self, result: ExecutionResult) -> None:
        with self._connect() as connection:
            connection.execute("""
                INSERT OR REPLACE INTO execution_history (
                    run_id, job_name, status, started_at, finished_at,
                    duration_seconds, output_json, error_type, error_message,
                    trigger
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.run_id,
                result.job_name,
                result.status,
                result.started_at.isoformat(),
                result.finished_at.isoformat(),
                result.duration_seconds,
                self._serialize_output(result.output),
                result.error_type,
                result.error_message,
                result.trigger,
            ))

    def get(self, run_id: str) -> ExecutionResult | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM execution_history WHERE run_id = ?",
                (run_id,),
            ).fetchone()

        return self._to_result(row) if row else None

    def list_runs(
        self,
        job_name: str | None = None,
        limit: int = 100,
    ) -> list[ExecutionResult]:
        if limit < 1:
            raise ValueError("Limit must be at least 1.")

        query = "SELECT * FROM execution_history"
        parameters: tuple = ()

        if job_name:
            query += " WHERE job_name = ?"
            parameters = (job_name,)

        query += " ORDER BY started_at DESC LIMIT ?"
        parameters += (limit,)

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._to_result(row) for row in rows]
