"""Test factor calculation interface."""

from datetime import datetime

import pandas as pd
import pytest

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)
from aistock.factors.registry import FactorRegistry, get_global_registry, register_factor


class MockFactorCalculator(FactorCalculator):
    """模拟因子计算器"""

    def __init__(self, name: str = "mock_factor"):
        self._name = name

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=self._name,
            description="Mock factor for testing",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            tags=["test", "mock"],
            data_requirements=["close", "volume"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算模拟因子"""
        start_time = datetime.now()

        # 简单计算：返回 close 的均值
        result_data = pd.DataFrame({
            "factor_value": data["close"].rolling(20).mean(),
        })

        calculation_time = (datetime.now() - start_time).total_seconds()

        return FactorResult(
            factor_name=self._name,
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class TestFactorMetadata:
    """测试 FactorMetadata"""

    def test_create_metadata(self):
        """测试创建元数据"""
        metadata = FactorMetadata(
            name="test_factor",
            description="Test factor",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
        )

        assert metadata.name == "test_factor"
        assert metadata.category == FactorCategory.TECHNICAL
        assert metadata.frequency == FactorFrequency.DAILY

    def test_to_dict(self):
        """测试转换为字典"""
        metadata = FactorMetadata(
            name="test_factor",
            description="Test factor",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            tags=["test"],
        )

        d = metadata.to_dict()
        assert d["name"] == "test_factor"
        assert d["category"] == "technical"
        # tags 被转换为字符串格式（Parquet 兼容性）
        assert "test" in d["tags"]


class TestFactorResult:
    """测试 FactorResult"""

    def test_create_result(self):
        """测试创建结果"""
        metadata = FactorMetadata(
            name="test_factor",
            description="Test factor",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
        )

        data = pd.DataFrame({"value": [1, 2, 3]})
        result = FactorResult(
            factor_name="test_factor",
            data=data,
            metadata=metadata,
            calculation_time=0.1,
        )

        assert result.factor_name == "test_factor"
        assert result.success is True
        assert result.calculation_time == 0.1

    def test_to_dict(self):
        """测试转换为字典"""
        metadata = FactorMetadata(
            name="test_factor",
            description="Test factor",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
        )

        data = pd.DataFrame({"value": [1, 2, 3]})
        result = FactorResult(
            factor_name="test_factor",
            data=data,
            metadata=metadata,
            calculation_time=0.1,
        )

        d = result.to_dict()
        assert d["factor_name"] == "test_factor"
        assert d["data_shape"] == (3, 1)
        assert d["success"] is True


class TestFactorCalculator:
    """测试 FactorCalculator"""

    def test_calculator_metadata(self):
        """测试计算器元数据"""
        calculator = MockFactorCalculator("test")
        metadata = calculator.metadata

        assert metadata.name == "test"
        assert metadata.category == FactorCategory.TECHNICAL

    def test_calculator_calculate(self):
        """测试计算器计算"""
        calculator = MockFactorCalculator("test")
        data = pd.DataFrame({
            "close": [10.0, 11.0, 12.0, 13.0, 14.0] * 5,
            "volume": [1000, 1100, 1200, 1300, 1400] * 5,
        })

        result = calculator.calculate(data)

        assert result.factor_name == "test"
        assert result.success is True
        assert len(result.data) == len(data)

    def test_calculator_repr(self):
        """测试计算器字符串表示"""
        calculator = MockFactorCalculator("test")
        assert "MockFactorCalculator" in repr(calculator)
        assert "test" in repr(calculator)


class TestFactorRegistry:
    """测试 FactorRegistry"""

    def test_register_factor(self):
        """测试注册因子"""
        registry = FactorRegistry()
        calculator = MockFactorCalculator("test")

        registry.register("test", calculator)

        assert "test" in registry
        assert len(registry) == 1

    def test_register_duplicate_factor(self):
        """测试注册重复因子"""
        registry = FactorRegistry()
        calculator = MockFactorCalculator("test")

        registry.register("test", calculator)

        with pytest.raises(ValueError, match="already registered"):
            registry.register("test", calculator)

    def test_unregister_factor(self):
        """测试注销因子"""
        registry = FactorRegistry()
        calculator = MockFactorCalculator("test")

        registry.register("test", calculator)
        registry.unregister("test")

        assert "test" not in registry
        assert len(registry) == 0

    def test_unregister_nonexistent_factor(self):
        """测试注销不存在的因子"""
        registry = FactorRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.unregister("test")

    def test_get_factor(self):
        """测试获取因子"""
        registry = FactorRegistry()
        calculator = MockFactorCalculator("test")

        registry.register("test", calculator)
        retrieved = registry.get("test")

        assert retrieved is calculator

    def test_get_nonexistent_factor(self):
        """测试获取不存在的因子"""
        registry = FactorRegistry()

        with pytest.raises(KeyError, match="not found"):
            registry.get("test")

    def test_get_metadata(self):
        """测试获取元数据"""
        registry = FactorRegistry()
        calculator = MockFactorCalculator("test")

        registry.register("test", calculator)
        metadata = registry.get_metadata("test")

        assert metadata.name == "test"

    def test_list_factors(self):
        """测试列出因子"""
        registry = FactorRegistry()
        registry.register("test1", MockFactorCalculator("test1"))
        registry.register("test2", MockFactorCalculator("test2"))

        factors = registry.list_factors()
        assert len(factors) == 2
        assert "test1" in factors
        assert "test2" in factors

    def test_list_factors_by_category(self):
        """测试按类别列出因子"""
        registry = FactorRegistry()
        registry.register("technical1", MockFactorCalculator("technical1"))

        # 创建一个基本面因子
        class FundamentalCalculator(FactorCalculator):
            @property
            def metadata(self):
                return FactorMetadata(
                    name="fundamental1",
                    description="Fundamental factor",
                    category=FactorCategory.FUNDAMENTAL,
                    frequency=FactorFrequency.QUARTERLY,
                )

            def calculate(self, data, params=None):
                return FactorResult(
                    factor_name="fundamental1",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                )

        registry.register("fundamental1", FundamentalCalculator())

        technical_factors = registry.list_factors(FactorCategory.TECHNICAL)
        assert len(technical_factors) == 1
        assert "technical1" in technical_factors

        fundamental_factors = registry.list_factors(FactorCategory.FUNDAMENTAL)
        assert len(fundamental_factors) == 1
        assert "fundamental1" in fundamental_factors

    def test_get_by_tag(self):
        """测试按标签获取因子"""
        registry = FactorRegistry()
        calculator = MockFactorCalculator("test")
        registry.register("test", calculator)

        factors = registry.get_by_tag("test")
        assert len(factors) == 1
        assert "test" in factors

    def test_registry_repr(self):
        """测试注册表字符串表示"""
        registry = FactorRegistry()
        assert "FactorRegistry" in repr(registry)
        assert "0" in repr(registry)


class TestGlobalRegistry:
    """测试全局注册表"""

    def test_get_global_registry(self):
        """测试获取全局注册表"""
        registry = get_global_registry()
        assert isinstance(registry, FactorRegistry)

    def test_register_factor_global(self):
        """测试全局注册因子"""
        # 清除全局注册表
        import aistock.factors.registry as registry_module
        registry_module._global_registry = None

        calculator = MockFactorCalculator("global_test")
        register_factor("global_test", calculator)

        registry = get_global_registry()
        assert "global_test" in registry

        # 清理
        registry.unregister("global_test")
