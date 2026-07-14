"""QuerySpec --- cross-backend unified query model."""

from dataclasses import dataclass
from datetime import date


@dataclass
class QuerySpec:
    """跨后端统一查询规格 --- 屏蔽 Parquet/SQL 差异"""

    schema: type
    asset_types: list[str] | None = None
    codes: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
    frequency: str | None = None
    columns: list[str] | None = None
    partition_keys: dict | None = None
