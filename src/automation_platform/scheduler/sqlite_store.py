"""SQLite storage for persistent automation schedules."""

import json
import sqlite3
from datetime import datetime, time
from pathlib import Path

from .models import ScheduleDefinition


class SQLiteScheduleStore:

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    from contextlib import contextmanager

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
                CREATE TABLE IF NOT EXISTS automation_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    job_name TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    interval_seconds INTEGER,
                    run_time TEXT,
                    weekdays_json TEXT NOT NULL,
                    next_run_at TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

    def save(
        self,
        schedule: ScheduleDefinition,
        next_run_at: datetime,
    ) -> None:
        with self._connect() as connection:
            connection.execute("""
                INSERT INTO automation_schedules (
                    schedule_id,
                    job_name,
                    frequency,
                    interval_seconds,
                    run_time,
                    weekdays_json,
                    next_run_at,
                    enabled,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(schedule_id) DO UPDATE SET
                    job_name = excluded.job_name,
                    frequency = excluded.frequency,
                    interval_seconds = excluded.interval_seconds,
                    run_time = excluded.run_time,
                    weekdays_json = excluded.weekdays_json,
                    next_run_at = excluded.next_run_at
            """, (
                schedule.schedule_id,
                schedule.job_name,
                schedule.frequency,
                schedule.interval_seconds,
                schedule.run_time.isoformat() if schedule.run_time else None,
                json.dumps(schedule.weekdays),
                next_run_at.isoformat(),
                datetime.now().astimezone().isoformat(),
            ))

    def get(self, schedule_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM automation_schedules
                WHERE schedule_id = ?
                """,
                (schedule_id,),
            ).fetchone()

        return dict(row) if row else None

    def list_schedules(self, enabled_only: bool = False) -> list[dict]:
        query = "SELECT * FROM automation_schedules"

        if enabled_only:
            query += " WHERE enabled = 1"

        query += " ORDER BY created_at"

        with self._connect() as connection:
            rows = connection.execute(query).fetchall()

        return [dict(row) for row in rows]

    def update_next_run(
        self,
        schedule_id: str,
        next_run_at: datetime,
    ) -> None:
        with self._connect() as connection:
            connection.execute("""
                UPDATE automation_schedules
                SET next_run_at = ?
                WHERE schedule_id = ?
            """, (next_run_at.isoformat(), schedule_id))

    def set_enabled(self, schedule_id: str, enabled: bool) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("""
                UPDATE automation_schedules
                SET enabled = ?
                WHERE schedule_id = ?
            """, (int(enabled), schedule_id))

        return cursor.rowcount > 0

    def remove(self, schedule_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("""
                DELETE FROM automation_schedules
                WHERE schedule_id = ?
            """, (schedule_id,))

        return cursor.rowcount > 0
