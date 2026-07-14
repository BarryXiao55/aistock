"""Factor normalization module."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


class FactorNormalizer:
    """因子标准化器"""

    def __init__(self):
        """初始化因子标准化器"""
        self._params: dict[str, dict] = {}

    def zscore(
        self,
        data: pd.Series,
        factor_name: str | None = None,
    ) -> pd.Series:
        """
        Z-Score 标准化。

        Args:
            data: 输入数据
            factor_name: 因子名称（用于保存参数）

        Returns:
            pd.Series: 标准化后的数据
        """
        mean = data.mean()
        std = data.std()

        if std == 0:
            result = pd.Series(0, index=data.index)
        else:
            result = (data - mean) / std

        # 保存参数
        if factor_name:
            self._params[factor_name] = {"mean": mean, "std": std}

        return result

    def minmax(
        self,
        data: pd.Series,
        factor_name: str | None = None,
    ) -> pd.Series:
        """
        MinMax 标准化。

        Args:
            data: 输入数据
            factor_name: 因子名称（用于保存参数）

        Returns:
            pd.Series: 标准化后的数据
        """
        min_val = data.min()
        max_val = data.max()

        if max_val == min_val:
            result = pd.Series(0.5, index=data.index)
        else:
            result = (data - min_val) / (max_val - min_val)

        # 保存参数
        if factor_name:
            self._params[factor_name] = {"min": min_val, "max": max_val}

        return result

    def rank(
        self,
        data: pd.Series,
        factor_name: str | None = None,
    ) -> pd.Series:
        """
        排名标准化。

        Args:
            data: 输入数据
            factor_name: 因子名称（用于保存参数）

        Returns:
            pd.Series: 标准化后的数据
        """
        result = data.rank(pct=True)
        return result

    def winsorize(
        self,
        data: pd.Series,
        lower_percentile: float = 0.01,
        upper_percentile: float = 0.99,
        factor_name: str | None = None,
    ) -> pd.Series:
        """
        Winsorize 标准化（缩尾处理）。

        Args:
            data: 输入数据
            lower_percentile: 下分位数
            upper_percentile: 上分位数
            factor_name: 因子名称（用于保存参数）

        Returns:
            pd.Series: 标准化后的数据
        """
        lower_bound = data.quantile(lower_percentile)
        upper_bound = data.quantile(upper_percentile)

        result = data.clip(lower=lower_bound, upper=upper_bound)

        # 保存参数
        if factor_name:
            self._params[factor_name] = {
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            }

        return result

    def get_params(self, factor_name: str) -> dict | None:
        """获取因子的标准化参数"""
        return self._params.get(factor_name)

    def save_params(self, file_path: str) -> None:
        """保存标准化参数"""
        import json
        with open(file_path, "w") as f:
            json.dump(self._params, f)

    def load_params(self, file_path: str) -> None:
        """加载标准化参数"""
        import json
        with open(file_path, "r") as f:
            self._params = json.load(f)
