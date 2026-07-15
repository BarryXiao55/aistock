"""Factor normalization utilities."""

import numpy as np
import pandas as pd
import time

from aistock.factors.interface import FactorCalculator, FactorMetadata, FactorResult, FactorCategory, FactorFrequency


class ZScoreNormalizer(FactorCalculator):
    """Z-Score 标准化因子"""

    def __init__(self, factor_name: str, factor_calculator: FactorCalculator):
        """
        初始化 Z-Score 标准化因子。

        Args:
            factor_name: 原始因子名称
            factor_calculator: 原始因子计算器
        """
        self._factor_name = factor_name
        self._factor_calculator = factor_calculator

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"{self._factor_name}_zscore",
            description=f"{self._factor_name} 的 Z-Score 标准化",
            category=self._factor_calculator.metadata.category,
            frequency=self._factor_calculator.metadata.frequency,
            version="1.0.0",
            tags=["normalization", "zscore"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 Z-Score 标准化"""
        start_time = time.time()

        # 计算原始因子
        original_result = self._factor_calculator.calculate(data, params)

        if not original_result.success:
            return original_result

        # 获取因子值
        factor_col = original_result.data.columns[0]
        factor_values = original_result.data[factor_col]

        # 计算 Z-Score
        mean = factor_values.mean()
        std = factor_values.std()

        if std > 0:
            zscore = (factor_values - mean) / std
        else:
            zscore = pd.Series(0, index=factor_values.index)

        result_data = pd.DataFrame({
            f"{self._factor_name}_zscore": zscore,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"{self._factor_name}_zscore",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class MinMaxNormalizer(FactorCalculator):
    """MinMax 标准化因子"""

    def __init__(self, factor_name: str, factor_calculator: FactorCalculator):
        """
        初始化 MinMax 标准化因子。

        Args:
            factor_name: 原始因子名称
            factor_calculator: 原始因子计算器
        """
        self._factor_name = factor_name
        self._factor_calculator = factor_calculator

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"{self._factor_name}_minmax",
            description=f"{self._factor_name} 的 MinMax 标准化",
            category=self._factor_calculator.metadata.category,
            frequency=self._factor_calculator.metadata.frequency,
            version="1.0.0",
            tags=["normalization", "minmax"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 MinMax 标准化"""
        start_time = time.time()

        # 计算原始因子
        original_result = self._factor_calculator.calculate(data, params)

        if not original_result.success:
            return original_result

        # 获取因子值
        factor_col = original_result.data.columns[0]
        factor_values = original_result.data[factor_col]

        # 计算 MinMax
        min_val = factor_values.min()
        max_val = factor_values.max()

        if max_val > min_val:
            minmax = (factor_values - min_val) / (max_val - min_val)
        else:
            minmax = pd.Series(0.5, index=factor_values.index)

        result_data = pd.DataFrame({
            f"{self._factor_name}_minmax": minmax,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"{self._factor_name}_minmax",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class RankNormalizer(FactorCalculator):
    """排名标准化因子"""

    def __init__(self, factor_name: str, factor_calculator: FactorCalculator):
        """
        初始化排名标准化因子。

        Args:
            factor_name: 原始因子名称
            factor_calculator: 原始因子计算器
        """
        self._factor_name = factor_name
        self._factor_calculator = factor_calculator

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"{self._factor_name}_rank",
            description=f"{self._factor_name} 的排名标准化",
            category=self._factor_calculator.metadata.category,
            frequency=self._factor_calculator.metadata.frequency,
            version="1.0.0",
            tags=["normalization", "rank"],
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算排名标准化"""
        start_time = time.time()

        # 计算原始因子
        original_result = self._factor_calculator.calculate(data, params)

        if not original_result.success:
            return original_result

        # 获取因子值
        factor_col = original_result.data.columns[0]
        factor_values = original_result.data[factor_col]

        # 计算排名百分比
        rank = factor_values.rank(pct=True)

        result_data = pd.DataFrame({
            f"{self._factor_name}_rank": rank,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"{self._factor_name}_rank",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
