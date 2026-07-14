"""Partition path derivation for Parquet storage."""

from pathlib import Path


def get_partition_path(
    base_dir: str | Path,
    schema: type,
    partition_keys: dict,
) -> Path:
    """
    根据 Schema 和分区键值生成分区路径。

    分区策略:
    - StockDailySchema: asset_type/freq/year/month/
    - StockMinuteSchema: asset_type/freq/year/month/
    - FinanceSchema: asset_type/report_period/
    - NorthFlowSchema: north_flow/year/month/
    - MarginTradeSchema: margin_trade/year/month/
    - AlternativeSchema: alt_{sub_type}/year/month/
    - ReferenceSchema: _reference/
    """
    base = Path(base_dir)

    # 根据 Schema 名称确定目录结构
    schema_name = schema.__name__

    if schema_name == "StockDailySchema":
        freq = partition_keys.get("frequency", "daily")
        return base / partition_keys["asset_type"] / freq / partition_keys["year"] / partition_keys["month"]

    elif schema_name == "StockMinuteSchema":
        freq = partition_keys.get("frequency", "1min")
        return base / partition_keys["asset_type"] / freq / partition_keys["year"] / partition_keys["month"]

    elif schema_name == "FinanceSchema":
        return base / partition_keys.get("asset_type", "stock") / "finance" / partition_keys["report_period"]

    elif schema_name == "NorthFlowSchema":
        return base / "north_flow" / partition_keys["year"] / partition_keys["month"]

    elif schema_name == "MarginTradeSchema":
        return base / "margin_trade" / partition_keys["year"] / partition_keys["month"]

    elif schema_name == "AlternativeSchema":
        sub_type = partition_keys.get("sub_type", "unknown")
        return base / f"alt_{sub_type}" / partition_keys["year"] / partition_keys["month"]

    elif schema_name == "ReferenceSchema":
        return base / "_reference"

    else:
        # 默认: 用 Schema 名称的小写形式
        dir_name = schema_name.replace("Schema", "").lower()
        return base / dir_name


def get_file_path(
    base_dir: str | Path,
    schema: type,
    partition_keys: dict,
    filename: str = "data.parquet",
) -> Path:
    """获取完整的文件路径"""
    partition_path = get_partition_path(base_dir, schema, partition_keys)
    return partition_path / filename
