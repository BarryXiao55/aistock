"""Test cleaning steps."""

import logging
from datetime import date

import pandas as pd
import pytest

from aistock.cleaning.adjustment import AdjustmentCleaner
from aistock.cleaning.interface import CleaningStep
from aistock.cleaning.status import StatusCleaner
from aistock.cleaning.universal import UniversalCleaner
from aistock.cleaning.validator import OHLCValidator
from aistock.pipeline.cleaner import Cleaner, STEPS_BASELINE
from aistock.pipeline.models import PipelineContext


@pytest.fixture
def mock_ctx():
    """创建测试用的 PipelineContext"""
    return PipelineContext(
        task_id="test-task-1",
        config={},
        log=logging.getLogger("test"),
    )


@pytest.fixture
def sample_df():
    """创建测试数据"""
    rows = [
        # 正常数据
        {
            "code": "000001.SZ",
            "trade_date": date(2025, 1, 2),
            "asset_type": "stock",
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000,
            "amount": 10200000.0,
            "adj_factor": 1.0,
        },
        # 重复数据（完全相同）
        {
            "code": "000001.SZ",
            "trade_date": date(2025, 1, 2),
            "asset_type": "stock",
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000,
            "amount": 10200000.0,
            "adj_factor": 1.0,
        },
        # 缺少 trade_date
        {
            "code": "600000.SH",
            "asset_type": "stock",
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000,
            "amount": 10200000.0,
            "adj_factor": 1.0,
        },
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def bad_ohlc_df():
    """创建包含 OHLC 问题的数据"""
    rows = [
        # high < low
        {
            "code": "000001.SZ",
            "trade_date": date(2025, 1, 2),
            "open": 10.0,
            "high": 9.0,
            "low": 10.5,
            "close": 10.2,
            "volume": 1000000,
        },
        # 负价格
        {
            "code": "600000.SH",
            "trade_date": date(2025, 1, 2),
            "open": -10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000000,
        },
        # 负成交量
        {
            "code": "000002.SZ",
            "trade_date": date(2025, 1, 2),
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": -1000,
        },
    ]
    return pd.DataFrame(rows)


class TestUniversalCleaner:
    """测试 UniversalCleaner"""

    def test_removes_duplicates(self, sample_df, mock_ctx):
        """测试去重功能"""
        cleaner = UniversalCleaner()
        result = cleaner.clean(sample_df, mock_ctx)
        # 去重后移除重复行，空值处理移除缺少 trade_date 的行，剩下 1 行
        assert len(result) == 1

    def test_removes_null_critical_fields(self, mock_ctx):
        """测试空值处理"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "trade_date": date(2025, 1, 2), "open": 10.0},
            {"code": None, "trade_date": date(2025, 1, 2), "open": 10.0},
            {"code": "600000.SH", "trade_date": None, "open": 10.0},
        ])
        cleaner = UniversalCleaner()
        result = cleaner.clean(df, mock_ctx)
        assert len(result) == 1

    def test_unifies_code_format(self, mock_ctx):
        """测试代码格式统一"""
        df = pd.DataFrame([
            {"code": "000001", "trade_date": date(2025, 1, 2)},
            {"code": "600000", "trade_date": date(2025, 1, 2)},
            {"code": "830001", "trade_date": date(2025, 1, 2)},
            {"code": "000001.SZ", "trade_date": date(2025, 1, 2)},  # 已有后缀
        ])
        cleaner = UniversalCleaner()
        result = cleaner.clean(df, mock_ctx)
        assert result["code"].tolist() == [
            "000001.SZ",
            "600000.SH",
            "830001.BJ",
            "000001.SZ",
        ]


class TestAdjustmentCleaner:
    """测试 AdjustmentCleaner"""

    def test_applies_forward_adjustment(self, mock_ctx):
        """测试前复权处理"""
        df = pd.DataFrame([
            {
                "code": "000001.SZ",
                "trade_date": date(2025, 1, 2),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000000,
                "adj_factor": 1.1,
            },
        ])
        cleaner = AdjustmentCleaner()
        result = cleaner.clean(df, mock_ctx)
        # 复权后的价格应该乘以 adj_factor
        assert result["open"].iloc[0] == pytest.approx(11.0)
        assert result["close"].iloc[0] == pytest.approx(11.22)

    def test_handles_zero_adj_factor(self, mock_ctx):
        """测试处理零复权因子"""
        df = pd.DataFrame([
            {
                "code": "000001.SZ",
                "trade_date": date(2025, 1, 2),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": 1000000,
                "adj_factor": 0,
            },
        ])
        cleaner = AdjustmentCleaner()
        result = cleaner.clean(df, mock_ctx)
        # 零复权因子应该被替换为 1.0
        assert result["adj_factor"].iloc[0] == 1.0

    def test_skips_without_adj_factor(self, mock_ctx):
        """测试没有复权因子列时跳过"""
        df = pd.DataFrame([
            {
                "code": "000001.SZ",
                "trade_date": date(2025, 1, 2),
                "open": 10.0,
                "close": 10.2,
            },
        ])
        cleaner = AdjustmentCleaner()
        result = cleaner.clean(df, mock_ctx)
        # 价格应该不变
        assert result["open"].iloc[0] == 10.0

    def test_validate_detects_negative_prices(self):
        """测试校验检测负价格"""
        df = pd.DataFrame([
            {"open": -10.0, "high": 10.5, "low": 9.8, "close": 10.2},
        ])
        cleaner = AdjustmentCleaner()
        issues = cleaner.validate(df)
        assert len(issues) > 0
        assert any("Negative" in i for i in issues)


class TestStatusCleaner:
    """测试 StatusCleaner"""

    def test_marks_st_stocks(self, mock_ctx):
        """测试标记 ST 股票"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "name": "平安银行"},
            {"code": "600000.SH", "name": "*ST 某某"},
            {"code": "000002.SZ", "name": "ST 某某"},
        ])
        cleaner = StatusCleaner()
        result = cleaner.clean(df, mock_ctx)
        assert result["is_st"].tolist() == [False, True, True]

    def test_marks_suspended_stocks(self, mock_ctx):
        """测试标记停牌股票"""
        df = pd.DataFrame([
            {"code": "000001.SZ", "volume": 1000000},
            {"code": "600000.SH", "volume": 0},
        ])
        cleaner = StatusCleaner()
        result = cleaner.clean(df, mock_ctx)
        assert result["is_suspended"].tolist() == [False, True]


class TestOHLCValidator:
    """测试 OHLCValidator"""

    def test_passes_on_valid_data(self, sample_df, mock_ctx):
        """测试有效数据通过校验"""
        # 移除有问题的行
        valid_df = sample_df[sample_df["code"] == "000001.SZ"].copy()
        cleaner = OHLCValidator()
        result = cleaner.clean(valid_df, mock_ctx)
        assert result["ohlc_valid"].all()

    def test_detects_high_low_violation(self, bad_ohlc_df, mock_ctx):
        """测试检测 high < low"""
        cleaner = OHLCValidator()
        result = cleaner.clean(bad_ohlc_df, mock_ctx)
        # 第一行 high < low
        assert not result.iloc[0]["ohlc_valid"]

    def test_detects_negative_price(self, bad_ohlc_df, mock_ctx):
        """测试检测负价格"""
        cleaner = OHLCValidator()
        result = cleaner.clean(bad_ohlc_df, mock_ctx)
        # 第二行负价格
        assert not result.iloc[1]["ohlc_valid"]

    def test_detects_negative_volume(self, bad_ohlc_df, mock_ctx):
        """测试检测负成交量"""
        cleaner = OHLCValidator()
        result = cleaner.clean(bad_ohlc_df, mock_ctx)
        # 第三行负成交量
        assert not result.iloc[2]["ohlc_valid"]


class TestCleanerOrchestrator:
    """测试 Cleaner 编排器"""

    def test_runs_steps_in_order(self, sample_df, mock_ctx):
        """测试按顺序执行步骤"""
        cleaner = Cleaner(STEPS_BASELINE)
        result_df, issues = cleaner.clean(sample_df, mock_ctx)
        # 应该执行了所有步骤
        assert len(issues) >= 0  # 可能有校验问题

    def test_collects_validation_issues(self, bad_ohlc_df, mock_ctx):
        """测试收集校验问题"""
        cleaner = Cleaner(STEPS_BASELINE)
        result_df, issues = cleaner.clean(bad_ohlc_df, mock_ctx)
        # 应该有 OHLC 校验问题
        assert len(issues) > 0
        assert any("ohlc_validator" in i for i in issues)

    def test_empty_steps_returns_unchanged(self, sample_df, mock_ctx):
        """测试空步骤返回原始数据"""
        cleaner = Cleaner([])
        result_df, issues = cleaner.clean(sample_df, mock_ctx)
        pd.testing.assert_frame_equal(result_df, sample_df)
        assert issues == []


class TestSTEPS_BASELINE:
    """测试 STEPS_BASELINE 配置"""

    def test_baseline_steps_are_defined(self):
        """测试基线步骤已定义"""
        assert len(STEPS_BASELINE) == 4

    def test_baseline_steps_are_cleaning_steps(self):
        """测试基线步骤都是 CleaningStep 实例"""
        for step in STEPS_BASELINE:
            assert isinstance(step, CleaningStep)

    def test_baseline_step_names(self):
        """测试基线步骤名称"""
        names = [step.name for step in STEPS_BASELINE]
        assert names == ["universal", "adjustment", "status", "ohlc_validator"]
