"""Adjustment cleaning step --- forward-adjusted price alignment."""

import pandas as pd

from aistock.cleaning.interface import CleaningStep


class AdjustmentCleaner(CleaningStep):
    """复权处理步骤：将后复权价格转换为前复权价格"""

    name = "adjustment"

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """执行复权处理"""
        # 如果没有复权因子列，跳过
        if "adj_factor" not in df.columns:
            ctx.log.info("No adj_factor column found, skipping adjustment")
            return df

        # 检查复权因子是否有效
        if (df["adj_factor"] == 0).any():
            ctx.log.warning("Found zero adj_factor values, replacing with 1.0")
            df["adj_factor"] = df["adj_factor"].replace(0, 1.0)

        # NaN 复权因子视为无复权
        if df["adj_factor"].isna().any():
            ctx.log.warning("Found NaN adj_factor values, replacing with 1.0")
            df["adj_factor"] = df["adj_factor"].fillna(1.0)

        # 计算前复权价格
        # 前复权价格 = 原始价格 * (当前复权因子 / 基准复权因子)
        # 这里假设 adj_factor 已经是相对于最新日期的复权因子
        price_columns = ["open", "high", "low", "close"]

        for col in price_columns:
            if col in df.columns:
                # 前复权：价格 * 复权因子
                df[f"{col}_adj"] = df[col] * df["adj_factor"]

        # 替换原始价格列为复权后的价格
        for col in price_columns:
            if f"{col}_adj" in df.columns:
                df[col] = df[f"{col}_adj"]
                df = df.drop(columns=[f"{col}_adj"])

        # 成交量也需要复权（反向）
        if "volume" in df.columns:
            df["volume"] = (df["volume"] / df["adj_factor"]).astype(int)

        ctx.log.info("Applied forward adjustment")
        return df

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验：检查复权后的价格是否合理"""
        issues = []

        if "adj_factor" in df.columns:
            # 检查复权因子是否为正
            if (df["adj_factor"] <= 0).any():
                issues.append("Non-positive adj_factor detected")

        # 检查复权后价格是否为正
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                if (df[col] < 0).any():
                    issues.append(f"Negative {col} after adjustment")

        return issues
