"""Factor storage and query module."""

from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from aistock.factors.interface import FactorMetadata


class FactorStorage:
    """因子存储管理器"""

    def __init__(self, base_dir: str | Path = "data/factors"):
        """
        初始化因子存储。

        Args:
            base_dir: 因子数据存储目录
        """
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        factor_name: str,
        data: pd.DataFrame,
        metadata: FactorMetadata,
        partition_keys: dict | None = None,
    ) -> str:
        """
        保存因子数据。

        Args:
            factor_name: 因子名称
            data: 因子数据 DataFrame
            metadata: 因子元数据
            partition_keys: 分区键（可选）

        Returns:
            str: 保存的文件路径
        """
        # 构建保存路径
        if partition_keys:
            partition_path = self._build_partition_path(factor_name, partition_keys)
        else:
            partition_path = self._base_dir / factor_name

        partition_path.mkdir(parents=True, exist_ok=True)

        # 保存数据
        file_path = partition_path / "data.parquet"
        data.to_parquet(file_path, engine="pyarrow")

        # 保存元数据
        metadata_path = partition_path / "metadata.parquet"
        metadata_df = pd.DataFrame([metadata.to_dict()])
        metadata_df.to_parquet(metadata_path, engine="pyarrow")

        return str(file_path)

    def load(
        self,
        factor_name: str,
        partition_keys: dict | None = None,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        加载因子数据。

        Args:
            factor_name: 因子名称
            partition_keys: 分区键（可选）
            columns: 要加载的列（可选，None 表示所有列）

        Returns:
            pd.DataFrame: 因子数据
        """
        # 构建文件路径
        if partition_keys:
            file_path = self._build_partition_path(factor_name, partition_keys) / "data.parquet"
        else:
            file_path = self._base_dir / factor_name / "data.parquet"

        if not file_path.exists():
            raise FileNotFoundError(f"Factor data not found: {file_path}")

        # 加载数据
        if columns:
            return pd.read_parquet(file_path, columns=columns, engine="pyarrow")
        else:
            return pd.read_parquet(file_path, engine="pyarrow")

    def load_metadata(self, factor_name: str) -> FactorMetadata:
        """
        加载因子元数据。

        Args:
            factor_name: 因子名称

        Returns:
            FactorMetadata: 因子元数据
        """
        metadata_path = self._base_dir / factor_name / "metadata.parquet"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Factor metadata not found: {metadata_path}")

        metadata_df = pd.read_parquet(metadata_path, engine="pyarrow")
        metadata_dict = metadata_df.iloc[0].to_dict()

        return FactorMetadata(
            name=metadata_dict["name"],
            description=metadata_dict["description"],
            category=metadata_dict["category"],
            frequency=metadata_dict["frequency"],
            version=metadata_dict.get("version", "1.0.0"),
            tags=metadata_dict.get("tags", []),
        )

    def exists(self, factor_name: str, partition_keys: dict | None = None) -> bool:
        """
        检查因子数据是否存在。

        Args:
            factor_name: 因子名称
            partition_keys: 分区键（可选）

        Returns:
            bool: 是否存在
        """
        if partition_keys:
            file_path = self._build_partition_path(factor_name, partition_keys) / "data.parquet"
        else:
            file_path = self._base_dir / factor_name / "data.parquet"

        return file_path.exists()

    def list_factors(self) -> list[str]:
        """
        列出所有已保存的因子。

        Returns:
            list[str]: 因子名称列表
        """
        factors = []
        for item in self._base_dir.iterdir():
            if item.is_dir() and (item / "data.parquet").exists():
                factors.append(item.name)
        return sorted(factors)

    def delete(self, factor_name: str, partition_keys: dict | None = None) -> None:
        """
        删除因子数据。

        Args:
            factor_name: 因子名称
            partition_keys: 分区键（可选）
        """
        if partition_keys:
            dir_path = self._build_partition_path(factor_name, partition_keys)
        else:
            dir_path = self._base_dir / factor_name

        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)

    def _build_partition_path(self, factor_name: str, partition_keys: dict) -> Path:
        """构建分区路径"""
        path_parts = [factor_name]
        for key, value in sorted(partition_keys.items()):
            path_parts.append(f"{key}={value}")
        return self._base_dir / "/".join(path_parts)


class FactorQuery:
    """因子查询接口"""

    def __init__(self, storage: FactorStorage):
        """
        初始化因子查询。

        Args:
            storage: 因子存储实例
        """
        self._storage = storage

    def query(
        self,
        factor_name: str,
        start_date: str | None = None,
        end_date: str | None = None,
        codes: list[str] | None = None,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        查询因子数据。

        Args:
            factor_name: 因子名称
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            codes: 股票代码列表（可选）
            columns: 要查询的列（可选）

        Returns:
            pd.DataFrame: 查询结果
        """
        # 加载数据
        df = self._storage.load(factor_name, columns=columns)

        # 应用过滤条件
        if start_date and "trade_date" in df.columns:
            df = df[df["trade_date"] >= start_date]

        if end_date and "trade_date" in df.columns:
            df = df[df["trade_date"] <= end_date]

        if codes and "code" in df.columns:
            df = df[df["code"].isin(codes)]

        return df

    def query_latest(
        self,
        factor_name: str,
        n: int = 1,
    ) -> pd.DataFrame:
        """
        查询最新的 n 条因子数据。

        Args:
            factor_name: 因子名称
            n: 返回的记录数

        Returns:
            pd.DataFrame: 最新的 n 条数据
        """
        df = self._storage.load(factor_name)

        if "trade_date" in df.columns:
            df = df.sort_values("trade_date", ascending=False)

        return df.head(n)
