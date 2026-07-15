"""Convertible bond specific cleaning step."""

import pandas as pd

from aistock.cleaning.interface import CleaningStep


class ConvertibleBondCleaner(CleaningStep):
    """可转债特定清洗步骤"""

    name = "convertible_bond"

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """执行可转债特定清洗"""
        # 1. 计算转股价值（如果没有）
        if "conversion_value" not in df.columns:
            if all(col in df.columns for col in ["close", "conversion_price"]):
                # 转股价值 = 正股价格 / 转股价格 * 100
                # 这里使用 close 作为近似正股价格
                cp_safe = df["conversion_price"].replace(0, float("nan"))
                df["conversion_value"] = (df["close"] / cp_safe) * 100

        # 2. 计算溢价率（如果没有）
        if "premium_rate" not in df.columns:
            if all(col in df.columns for col in ["close", "conversion_value"]):
                # 溢价率 = (可转债价格 - 转股价值) / 转股价值 * 100
                df["premium_rate"] = ((df["close"] - df["conversion_value"]) / df["conversion_value"]) * 100

        # 3. 标记高溢价率可转债（>50%）
        if "premium_rate" in df.columns:
            df["high_premium"] = df["premium_rate"] > 50
            high_premium_count = df["high_premium"].sum()
            if high_premium_count > 0:
                ctx.log.info(f"Marked {high_premium_count} high premium convertible bonds")

        # 4. 标记临近到期可转债（<1年）
        if "maturity_date" in df.columns:
            from datetime import date, timedelta
            one_year_later = date.today() + timedelta(days=365)
            df["near_maturity"] = pd.to_datetime(df["maturity_date"]).dt.date <= one_year_later
            near_maturity_count = df["near_maturity"].sum()
            if near_maturity_count > 0:
                ctx.log.info(f"Marked {near_maturity_count} near-maturity convertible bonds")

        return df

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验"""
        issues = []

        # 检查转股价格合理性
        if "conversion_price" in df.columns:
            if (df["conversion_price"] <= 0).any():
                issues.append("Non-positive conversion_price detected")

        # 检查溢价率范围
        if "premium_rate" in df.columns:
            if (df["premium_rate"] < -50).any() or (df["premium_rate"] > 500).any():
                issues.append("premium_rate out of reasonable range")

        return issues
