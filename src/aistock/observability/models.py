"""Observability data models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TaskRun:
    """任务运行记录"""

    id: str
    started_at: datetime
    finished_at: datetime | None = None
    source_name: str = ""
    spec_json: str = ""
    status: str = ""  # "success" | "partial" | "failed"
    records_fetched: int = 0
    records_after_clean: int = 0
    records_written: int = 0
    duration_ms: int = 0
    issues_json: str = ""
    fallback_used: str | None = None
    failed_codes_json: str = ""


@dataclass
class DataSnapshot:
    """数据快照记录"""

    date: str
    schema_name: str
    partition_key: str
    record_count: int
    source_name: str
    checksum: str = ""
