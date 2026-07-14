"""Parquet storage backend implementation."""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from aistock.exceptions import BackendUnavailable, WriteError
from aistock.storage.interface import StorageBackend
from aistock.storage.parquet.partition import get_file_path, get_partition_path


class ParquetBackend(StorageBackend):
    """Parquet 文件存储后端"""

    name = "parquet"

    def __init__(self, config: dict):
        self._config = config
        self._base_dir = Path(config.get("data_dir", "data")) / "parquet"
        self._compression = config.get("storage", {}).get("compression", "zstd")
        self._compression_level = config.get("storage", {}).get("compression_level", 3)

    def write(self, df: pd.DataFrame, schema: type, partition_keys: dict) -> "WriteResult":
        """全量写入，覆盖已有分区"""
        from aistock.pipeline.models import WriteResult

        try:
            file_path = get_file_path(self._base_dir, schema, partition_keys)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换为 PyArrow Table 并写入
            table = pa.Table.from_pandas(df)

            # 根据压缩算法决定是否使用 compression_level
            # snappy 和 gzip 不支持 compression_level
            write_kwargs = {
                "table": table,
                "where": file_path,
                "compression": self._compression,
            }

            if self._compression not in ("snappy", "gzip", "none"):
                write_kwargs["compression_level"] = self._compression_level

            pq.write_table(**write_kwargs)

            return WriteResult(
                records_written=len(df),
                partitions_affected=[str(file_path)],
                backend=self.name,
            )
        except Exception as e:
            raise WriteError(f"Failed to write to Parquet: {e}") from e

    def read(self, query) -> pd.DataFrame:
        """按条件读取"""
        try:
            schema = query.schema
            partition_keys = query.partition_keys or {}

            if partition_keys:
                # 精确分区命中
                file_path = get_file_path(self._base_dir, schema, partition_keys)
                if not file_path.exists():
                    return pd.DataFrame()

                df = pd.read_parquet(file_path)
            else:
                # 扫描目录
                partition_path = get_partition_path(self._base_dir, schema, partition_keys)
                if not partition_path.exists():
                    return pd.DataFrame()

                dfs = []
                for parquet_file in partition_path.rglob("*.parquet"):
                    dfs.append(pd.read_parquet(parquet_file))

                if not dfs:
                    return pd.DataFrame()
                df = pd.concat(dfs, ignore_index=True)

            # 应用过滤条件
            if query.codes:
                df = df[df["code"].isin(query.codes)]

            if query.start_date:
                date_col = "trade_date" if "trade_date" in df.columns else "trade_time"
                df = df[df[date_col] >= query.start_date]

            if query.end_date:
                date_col = "trade_date" if "trade_date" in df.columns else "trade_time"
                df = df[df[date_col] <= query.end_date]

            if query.columns:
                df = df[query.columns]

            return df

        except Exception as e:
            raise BackendUnavailable(f"Failed to read from Parquet: {e}") from e

    def upsert(
        self,
        df: pd.DataFrame,
        schema: type,
        partition_keys: dict,
        on_conflict: list[str],
    ) -> "WriteResult":
        """按主键去重更新"""
        from aistock.pipeline.models import WriteResult

        try:
            file_path = get_file_path(self._base_dir, schema, partition_keys)

            if file_path.exists():
                # 读取现有数据
                existing_df = pd.read_parquet(file_path)

                # 合并并去重
                combined = pd.concat([existing_df, df], ignore_index=True)
                combined = combined.drop_duplicates(subset=on_conflict, keep="last")
                df = combined

            # 写入
            return self.write(df, schema, partition_keys)

        except Exception as e:
            raise WriteError(f"Failed to upsert to Parquet: {e}") from e

    def exists(self, schema: type, partition_keys: dict) -> bool:
        """检查指定分区是否已有数据"""
        try:
            file_path = get_file_path(self._base_dir, schema, partition_keys)
            return file_path.exists()
        except Exception:
            return False
