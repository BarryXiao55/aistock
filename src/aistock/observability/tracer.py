"""Task metadata tracer --- SQLite storage for pipeline runs."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from aistock.observability.models import DataSnapshot, TaskRun


class TaskTracer:
    """任务元数据追踪器"""

    def __init__(self, db_path: str = "data/meta/data_pipeline.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_runs (
                    id TEXT PRIMARY KEY,
                    started_at TEXT,
                    finished_at TEXT,
                    source_name TEXT,
                    spec_json TEXT,
                    status TEXT,
                    records_fetched INTEGER,
                    records_after_clean INTEGER,
                    records_written INTEGER,
                    duration_ms INTEGER,
                    issues_json TEXT,
                    fallback_used TEXT,
                    failed_codes_json TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_snapshots (
                    date TEXT,
                    schema_name TEXT,
                    partition_key TEXT,
                    record_count INTEGER,
                    source_name TEXT,
                    checksum TEXT,
                    PRIMARY KEY (date, schema_name, partition_key)
                )
            """)

    def start_task(self, task_id: str, spec_json: str = "") -> TaskRun:
        """开始一个新任务"""
        task = TaskRun(
            id=task_id,
            started_at=datetime.now(),
            spec_json=spec_json,
            status="running",
        )

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO task_runs (id, started_at, spec_json, status)
                VALUES (?, ?, ?, ?)
                """,
                (task.id, task.started_at.isoformat(), task.spec_json, task.status),
            )

        return task

    def finish_task(self, task: TaskRun):
        """完成一个任务"""
        task.finished_at = datetime.now()

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO task_runs
                (id, started_at, finished_at, source_name, spec_json, status,
                 records_fetched, records_after_clean, records_written, duration_ms,
                 issues_json, fallback_used, failed_codes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.started_at.isoformat(),
                    task.finished_at.isoformat(),
                    task.source_name,
                    task.spec_json,
                    task.status,
                    task.records_fetched,
                    task.records_after_clean,
                    task.records_written,
                    task.duration_ms,
                    task.issues_json if isinstance(task.issues_json, str) else json.dumps(task.issues_json, ensure_ascii=False),
                    task.fallback_used,
                    task.failed_codes_json if isinstance(task.failed_codes_json, str) else json.dumps(task.failed_codes_json, ensure_ascii=False),
                ),
            )

    def get_task(self, task_id: str) -> TaskRun | None:
        """获取任务信息"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM task_runs WHERE id = ?", (task_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return TaskRun(
                id=row[0],
                started_at=datetime.fromisoformat(row[1]),
                finished_at=datetime.fromisoformat(row[2]) if row[2] else None,
                source_name=row[3],
                spec_json=row[4],
                status=row[5],
                records_fetched=row[6],
                records_after_clean=row[7],
                records_written=row[8],
                duration_ms=row[9],
                issues_json=row[10],
                fallback_used=row[11],
                failed_codes_json=row[12],
            )

    def get_recent_tasks(self, limit: int = 10) -> list[TaskRun]:
        """获取最近的任务列表"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM task_runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()

            tasks = []
            for row in rows:
                tasks.append(
                    TaskRun(
                        id=row[0],
                        started_at=datetime.fromisoformat(row[1]),
                        finished_at=datetime.fromisoformat(row[2]) if row[2] else None,
                        source_name=row[3],
                        spec_json=row[4],
                        status=row[5],
                        records_fetched=row[6],
                        records_after_clean=row[7],
                        records_written=row[8],
                        duration_ms=row[9],
                        issues_json=row[10],
                        fallback_used=row[11],
                        failed_codes_json=row[12],
                    )
                )

            return tasks

    def add_snapshot(self, snapshot: DataSnapshot):
        """添加数据快照"""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_snapshots
                (date, schema_name, partition_key, record_count, source_name, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.date,
                    snapshot.schema_name,
                    snapshot.partition_key,
                    snapshot.record_count,
                    snapshot.source_name,
                    snapshot.checksum,
                ),
            )

    def get_snapshots(self, schema_name: str | None = None) -> list[DataSnapshot]:
        """获取数据快照"""
        with sqlite3.connect(self._db_path) as conn:
            if schema_name:
                cursor = conn.execute(
                    "SELECT * FROM data_snapshots WHERE schema_name = ?",
                    (schema_name,),
                )
            else:
                cursor = conn.execute("SELECT * FROM data_snapshots")

            rows = cursor.fetchall()

            return [
                DataSnapshot(
                    date=row[0],
                    schema_name=row[1],
                    partition_key=row[2],
                    record_count=row[3],
                    source_name=row[4],
                    checksum=row[5],
                )
                for row in rows
            ]
