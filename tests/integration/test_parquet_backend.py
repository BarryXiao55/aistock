"""Test Parquet storage backend."""

import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from aistock.schemas.daily import StockDailySchema
from aistock.schemas.finance import FinanceSchema
from aistock.storage.parquet.backend import ParquetBackend
from aistock.storage.parquet.partition import get_file_path, get_partition_path
from aistock.storage.query import QuerySpec


class TestPartition:
    """测试分区路径生成"""

    def test_daily_partition_path(self):
        """测试日线分区路径"""
        partition_keys = {
            "asset_type": "stock",
            "year": "2025",
            "month": "01",
        }
        path = get_partition_path("/data/parquet", StockDailySchema, partition_keys)
        assert path == Path("/data/parquet/stock/daily/2025/01")

    def test_finance_partition_path(self):
        """测试财务数据分区路径"""
        partition_keys = {
            "asset_type": "stock",
            "report_period": "2025Q1",
        }
        path = get_partition_path("/data/parquet", FinanceSchema, partition_keys)
        assert path == Path("/data/parquet/stock/finance/2025Q1")

    def test_daily_file_path(self):
        """测试日线文件路径"""
        partition_keys = {
            "asset_type": "stock",
            "year": "2025",
            "month": "01",
        }
        path = get_file_path("/data/parquet", StockDailySchema, partition_keys)
        assert path == Path("/data/parquet/stock/daily/2025/01/data.parquet")


class TestParquetBackend:
    """测试 Parquet 后端"""

    @pytest.fixture
    def backend(self, tmp_path):
        """创建临时后端实例"""
        config = {
            "data_dir": str(tmp_path),
            "storage": {
                "backend": "parquet",
                "compression": "snappy",
            },
        }
        return ParquetBackend(config)

    @pytest.fixture
    def sample_df(self):
        """创建测试数据"""
        rows = []
        for code in ["000001.SZ", "600000.SH"]:
            for d in [date(2025, 1, 2), date(2025, 1, 3)]:
                rows.append({
                    "code": code,
                    "trade_date": d,
                    "asset_type": "stock",
                    "open": 10.0,
                    "high": 10.5,
                    "low": 9.8,
                    "close": 10.2,
                    "volume": 1000000,
                    "amount": 10200000.0,
                    "adj_factor": 1.0,
                    "is_st": False,
                    "is_suspended": False,
                })
        return pd.DataFrame(rows)

    def test_write_and_read_roundtrip(self, backend, sample_df):
        """测试写入后读取"""
        partition_keys = {
            "asset_type": "stock",
            "year": "2025",
            "month": "01",
        }

        # 写入
        result = backend.write(sample_df, StockDailySchema, partition_keys)
        assert result.records_written == 4
        assert result.backend == "parquet"

        # 读取
        query = QuerySpec(
            schema=StockDailySchema,
            partition_keys=partition_keys,
        )
        df_read = backend.read(query)
        assert len(df_read) == 4
        assert list(df_read.columns) == list(sample_df.columns)

    def test_exists(self, backend, sample_df):
        """测试 exists 方法"""
        partition_keys = {
            "asset_type": "stock",
            "year": "2025",
            "month": "01",
        }

        # 写入前不存在
        assert not backend.exists(StockDailySchema, partition_keys)

        # 写入后存在
        backend.write(sample_df, StockDailySchema, partition_keys)
        assert backend.exists(StockDailySchema, partition_keys)

    def test_upsert_updates_existing(self, backend, sample_df):
        """测试 upsert 更新现有数据"""
        partition_keys = {
            "asset_type": "stock",
            "year": "2025",
            "month": "01",
        }

        # 写入初始数据
        backend.write(sample_df, StockDailySchema, partition_keys)

        # 创建更新数据
        updated_df = sample_df.copy()
        updated_df.loc[0, "close"] = 11.0  # 修改第一条记录的价格

        # upsert
        result = backend.upsert(
            updated_df,
            StockDailySchema,
            partition_keys,
            on_conflict=["code", "trade_date"],
        )
        assert result.records_written == 4

        # 验证更新
        query = QuerySpec(
            schema=StockDailySchema,
            partition_keys=partition_keys,
        )
        df_read = backend.read(query)
        # 第一条记录的 close 应该是 11.0
        first_row = df_read[df_read["code"] == "000001.SZ"].iloc[0]
        assert first_row["close"] == 11.0

    def test_read_nonexistent_partition(self, backend):
        """测试读取不存在的分区"""
        partition_keys = {
            "asset_type": "stock",
            "year": "2099",
            "month": "12",
        }
        query = QuerySpec(
            schema=StockDailySchema,
            partition_keys=partition_keys,
        )
        df = backend.read(query)
        assert len(df) == 0

    def test_read_with_code_filter(self, backend, sample_df):
        """测试按代码过滤读取"""
        partition_keys = {
            "asset_type": "stock",
            "year": "2025",
            "month": "01",
        }
        backend.write(sample_df, StockDailySchema, partition_keys)

        query = QuerySpec(
            schema=StockDailySchema,
            partition_keys=partition_keys,
            codes=["000001.SZ"],
        )
        df = backend.read(query)
        assert len(df) == 2
        assert all(df["code"] == "000001.SZ")

    def test_read_with_date_filter(self, backend, sample_df):
        """测试按日期过滤读取"""
        partition_keys = {
            "asset_type": "stock",
            "year": "2025",
            "month": "01",
        }
        backend.write(sample_df, StockDailySchema, partition_keys)

        query = QuerySpec(
            schema=StockDailySchema,
            partition_keys=partition_keys,
            start_date=date(2025, 1, 3),
        )
        df = backend.read(query)
        assert len(df) == 2
        assert all(df["trade_date"] == date(2025, 1, 3))

    def test_write_multiple_partitions(self, backend, sample_df):
        """测试写入多个分区"""
        # 写入 2025-01
        partition_keys_1 = {
            "asset_type": "stock",
            "year": "2025",
            "month": "01",
        }
        backend.write(sample_df, StockDailySchema, partition_keys_1)

        # 写入 2025-02
        partition_keys_2 = {
            "asset_type": "stock",
            "year": "2025",
            "month": "02",
        }
        backend.write(sample_df, StockDailySchema, partition_keys_2)

        # 验证两个分区都存在
        assert backend.exists(StockDailySchema, partition_keys_1)
        assert backend.exists(StockDailySchema, partition_keys_2)
