"""Factor analyzer for evaluating factor quality."""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class FactorAnalysisResult:
    """因子分析结果"""
    factor_name: str
    ic_mean: float  # 平均信息系数
    ic_std: float  # 信息系数标准差
    ir: float  # 信息比率 (IC_mean / IC_std)
    turnover_mean: float  # 平均换手率
    return_mean: float  # 平均收益
    return_std: float  # 收益标准差
    sharpe_ratio: float  # 夏普比率
    max_drawdown: float  # 最大回撤
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "factor_name": self.factor_name,
            "ic_mean": self.ic_mean,
            "ic_std": self.ic_std,
            "ir": self.ir,
            "turnover_mean": self.turnover_mean,
            "return_mean": self.return_mean,
            "return_std": self.return_std,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "details": self.details,
        }


class FactorAnalyzer:
    """因子分析器"""

    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化因子分析器。

        Args:
            risk_free_rate: 无风险收益率（年化）
        """
        self.risk_free_rate = risk_free_rate

    def analyze(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series,
        holding_period: int = 5,
    ) -> FactorAnalysisResult:
        """
        分析因子质量。

        Args:
            factor_values: 因子值序列
            forward_returns: 前瞻收益序列
            holding_period: 持有期（交易日数）

        Returns:
            FactorAnalysisResult: 分析结果
        """
        # 对齐数据
        common_index = factor_values.index.intersection(forward_returns.index)
        factor_values = factor_values.loc[common_index]
        forward_returns = forward_returns.loc[common_index]

        # 计算 IC (Information Coefficient)
        ic_mean, ic_std = self._calculate_ic(factor_values, forward_returns)

        # 计算 IR (Information Ratio)
        ir = ic_mean / ic_std if ic_std > 0 else 0.0

        # 计算换手率
        turnover_mean = self._calculate_turnover(factor_values)

        # 计算收益统计
        return_mean, return_std = self._calculate_return_stats(forward_returns)

        # 计算夏普比率
        sharpe_ratio = self._calculate_sharpe(forward_returns)

        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(forward_returns)

        return FactorAnalysisResult(
            factor_name="analyzed_factor",
            ic_mean=ic_mean,
            ic_std=ic_std,
            ir=ir,
            turnover_mean=turnover_mean,
            return_mean=return_mean,
            return_std=return_std,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            details={
                "data_points": len(common_index),
                "holding_period": holding_period,
            },
        )

    def _calculate_ic(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series,
    ) -> tuple[float, float]:
        """计算 IC (Information Coefficient)"""
        # 按日期分组计算 IC
        if isinstance(factor_values.index, pd.DatetimeIndex):
            # 按日期分组
            ic_values = []
            for date in factor_values.index.unique():
                factor_day = factor_values[factor_values.index == date]
                returns_day = forward_returns[forward_returns.index == date]

                if len(factor_day) > 1 and len(returns_day) > 1:
                    # 计算截面相关系数
                    correlation = factor_day.corr(returns_day)
                    if not np.isnan(correlation):
                        ic_values.append(correlation)

            if ic_values:
                return np.mean(ic_values), np.std(ic_values)
            else:
                return 0.0, 0.0
        else:
            # 简单相关系数
            ic = factor_values.corr(forward_returns)
            return ic if not np.isnan(ic) else 0.0, 0.0

    def _calculate_turnover(self, factor_values: pd.Series) -> float:
        """计算换手率"""
        if len(factor_values) < 2:
            return 0.0

        # 计算排名变化
        rank_today = factor_values.rank(pct=True)
        rank_yesterday = rank_today.shift(1)

        # 计算换手率 = |排名变化| 的均值
        turnover = (rank_today - rank_yesterday).abs().mean()
        return turnover if not np.isnan(turnover) else 0.0

    def _calculate_return_stats(
        self,
        forward_returns: pd.Series,
    ) -> tuple[float, float]:
        """计算收益统计"""
        return_mean = forward_returns.mean()
        return_std = forward_returns.std()
        return return_mean, return_std

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        if len(returns) == 0:
            return 0.0

        return_mean = returns.mean()
        return_std = returns.std()

        if return_std == 0:
            return 0.0

        # 年化夏普比率
        sharpe = (return_mean - self.risk_free_rate / 252) / return_std * np.sqrt(252)
        return sharpe

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        if len(returns) == 0:
            return 0.0

        # 计算累计收益
        cumulative = (1 + returns).cumprod()

        # 计算回撤
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max

        # 最大回撤
        max_drawdown = drawdown.min()
        return max_drawdown

    def analyze_by_group(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series,
        groups: pd.Series,
    ) -> dict[str, FactorAnalysisResult]:
        """
        按分组分析因子。

        Args:
            factor_values: 因子值序列
            forward_returns: 前瞻收益序列
            groups: 分组标签序列

        Returns:
            dict: 分组分析结果
        """
        results = {}
        for group in groups.unique():
            mask = groups == group
            group_factor = factor_values[mask]
            group_returns = forward_returns[mask]

            if len(group_factor) > 0:
                result = self.analyze(group_factor, group_returns)
                results[str(group)] = result

        return results
