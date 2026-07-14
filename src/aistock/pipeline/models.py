"""Pipeline data models."""

from dataclasses import dataclass, field
from datetime import date
from logging import Logger


@dataclass
class FetchSpec:
    """一次数据抓取的规格"""

    asset_type: str
    codes: list[str] | None
    start_date: date
    end_date: date
    schema: type
    frequency: str = "daily"


@dataclass
class PipelineContext:
    """贯穿一次管道运行的上下文"""

    task_id: str
    config: dict
    log: Logger


@dataclass
class WriteResult:
    """存储写入结果"""

    records_written: int
    partitions_affected: list[str]
    backend: str


@dataclass
class PipelineReport:
    """一次管道运行的完整报告"""

    task_id: str
    source_name: str
    status: str  # "success" | "partial" | "failed"
    records_fetched: int
    records_after_clean: int
    records_written: int
    duration_ms: int
    issues: list[str] = field(default_factory=list)
    failed_codes: list[str] = field(default_factory=list)
    fallback_used: str | None = None
