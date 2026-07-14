"""Test project structure and imports."""

import pytest


class TestProjectStructure:
    """测试项目结构"""

    def test_import_aistock(self):
        """测试 aistock 包可以导入"""
        import aistock

        assert aistock.__version__ == "0.1.0"

    def test_import_exceptions(self):
        """测试异常模块可以导入"""
        from aistock.exceptions import (
            PipelineError,
            SourceError,
            SourceUnavailable,
            SourceRateLimited,
            CleanError,
            ValidationError,
            StoreError,
            WriteError,
            BackendUnavailable,
        )

        # 验证异常层级
        assert issubclass(SourceError, PipelineError)
        assert issubclass(CleanError, PipelineError)
        assert issubclass(StoreError, PipelineError)
        assert issubclass(SourceUnavailable, SourceError)
        assert issubclass(SourceRateLimited, SourceError)
        assert issubclass(ValidationError, CleanError)
        assert issubclass(WriteError, StoreError)
        assert issubclass(BackendUnavailable, StoreError)

    def test_import_schemas(self):
        """测试 Schema 模块可以导入"""
        from aistock.schemas import SCHEMA_REGISTRY
        from aistock.schemas.daily import StockDailySchema
        from aistock.schemas.minute import StockMinuteSchema
        from aistock.schemas.finance import FinanceSchema
        from aistock.schemas.alternative import (
            AlternativeSchema,
            NorthFlowSchema,
            MarginTradeSchema,
        )
        from aistock.schemas.reference import ReferenceSchema

        # 验证注册表
        assert SCHEMA_REGISTRY["daily"] is StockDailySchema
        assert SCHEMA_REGISTRY["minute"] is StockMinuteSchema
        assert SCHEMA_REGISTRY["finance"] is FinanceSchema
        assert SCHEMA_REGISTRY["alternative"] is AlternativeSchema
        assert SCHEMA_REGISTRY["north_flow"] is NorthFlowSchema
        assert SCHEMA_REGISTRY["margin_trade"] is MarginTradeSchema
        assert SCHEMA_REGISTRY["reference"] is ReferenceSchema

    def test_import_pipeline(self):
        """测试管道模块可以导入"""
        from aistock.pipeline.models import FetchSpec, PipelineContext, PipelineReport, WriteResult
        from aistock.pipeline.source import SourceNode
        from aistock.pipeline.cleaner import Cleaner
        from aistock.pipeline.runner import PipelineRunner

        # 验证类存在
        assert FetchSpec is not None
        assert PipelineContext is not None
        assert PipelineReport is not None
        assert WriteResult is not None
        assert SourceNode is not None
        assert Cleaner is not None
        assert PipelineRunner is not None

    def test_import_storage(self):
        """测试存储模块可以导入"""
        from aistock.storage.interface import StorageBackend
        from aistock.storage.query import QuerySpec
        from aistock.storage.router import get_backend

        # 验证类存在
        assert StorageBackend is not None
        assert QuerySpec is not None
        assert callable(get_backend)

    def test_import_sources(self):
        """测试数据源模块可以导入"""
        from aistock.sources.registry import SourceRegistry

        # 验证类存在
        assert SourceRegistry is not None

    def test_import_cleaning(self):
        """测试清洗模块可以导入"""
        from aistock.cleaning.interface import CleaningStep

        # 验证类存在
        assert CleaningStep is not None
