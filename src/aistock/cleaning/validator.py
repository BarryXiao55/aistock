"""Validator cleaning step --- OHLC sanity checks."""

import pandas as pd

from aistock.cleaning.interface import CleaningStep


class OHLCValidator(CleaningStep):
    """OHLC 校验步骤：检查价格和成交量的合理性"""

    name = "ohlc_validator"

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """执行 OHLC 校验（仅标记，不删除）"""
        # 检查必需的列是否存在
        required_columns = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            ctx.log.warning(f"Missing columns for OHLC validation: {missing}")
            return df

        # 初始化校验结果列
        df["ohlc_valid"] = True

        # 1. 检查 high >= low
        high_low_violation = df["high"] < df["low"]
        if high_low_violation.any():
            df.loc[high_low_violation, "ohlc_valid"] = False
            ctx.log.warning(f"Found {high_low_violation.sum()} rows with high < low")

        # 2. 检查 high >= open 和 high >= close
        high_violation = (df["high"] < df["open"]) | (df["high"] < df["close"])
        if high_violation.any():
            df.loc[high_violation, "ohlc_valid"] = False
            ctx.log.warning(f"Found {high_violation.sum()} rows with high < open or high < close")

        # 3. 检查 low <= open 和 low <= close
        low_violation = (df["low"] > df["open"]) | (df["low"] > df["close"])
        if low_violation.any():
            df.loc[low_violation, "ohlc_valid"] = False
            ctx.log.warning(f"Found {low_violation.sum()} rows with low > open or low > close")

        # 4. 检查价格非负
        price_columns = ["open", "high", "low", "close"]
        for col in price_columns:
            negative = df[col] < 0
            if negative.any():
                df.loc[negative, "ohlc_valid"] = False
                ctx.log.warning(f"Found {negative.sum()} rows with negative {col}")

        # 5. 检查成交量非负
        negative_volume = df["volume"] < 0
        if negative_volume.any():
            df.loc[negative_volume, "ohlc_valid"] = False
            ctx.log.warning(f"Found {negative_volume.sum()} rows with negative volume")

        # 6. 检查成交额非负
        if "amount" in df.columns:
            negative_amount = df["amount"] < 0
            if negative_amount.any():
                df.loc[negative_amount, "ohlc_valid"] = False
                ctx.log.warning(f"Found {negative_amount.sum()} rows with negative amount")

        return df

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验：检查校验结果"""
        issues = []

        if "ohlc_valid" in df.columns:
            invalid_count = (~df["ohlc_valid"]).sum()
            if invalid_count > 0:
                issues.append(f"Found {invalid_count} rows with OHLC validation errors")

        return issues
