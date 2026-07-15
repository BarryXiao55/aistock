"""Futures specific cleaning step."""

import pandas as pd

from aistock.cleaning.interface import CleaningStep


class FuturesCleaner(CleaningStep):
    """期货特定清洗步骤"""

    name = "futures"

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """执行期货特定清洗"""
        # 1. 标记主力合约
        if "volume" in df.columns and "code" in df.columns:
            # 按日期分组，找到每日成交量最大的合约
            if not df.empty and "trade_date" in df.columns:
                daily_max = df.groupby("trade_date")["volume"].transform("max")
                df["is_main_contract"] = df["volume"] == daily_max
                main_count = df["is_main_contract"].sum()
                if main_count > 0:
                    ctx.log.info(f"Marked {main_count} main contract records")

        # 2. 标记临近交割月合约（<1个月）
        if "expiry_date" in df.columns:
            from datetime import date, timedelta
            one_month_later = date.today() + timedelta(days=30)
            df["near_delivery"] = pd.to_datetime(df["expiry_date"]).dt.date <= one_month_later
            near_delivery_count = df["near_delivery"].sum()
            if near_delivery_count > 0:
                ctx.log.info(f"Marked {near_delivery_count} near-delivery contracts")

        # 3. 计算持仓量变化（如果有历史数据）
        if "open_interest" in df.columns and "code" in df.columns:
            if not df.empty and "trade_date" in df.columns:
                df = df.sort_values(["code", "trade_date"])
                df["oi_change"] = df.groupby("code")["open_interest"].diff()
                df["oi_change"] = df["oi_change"].fillna(0)

        return df

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验"""
        issues = []

        # 检查保证金比例合理性
        if "margin_rate" in df.columns:
            if (df["margin_rate"] < 0).any() or (df["margin_rate"] > 100).any():
                issues.append("margin_rate out of reasonable range")

        # 检查合约乘数
        if "contract_multiplier" in df.columns:
            if (df["contract_multiplier"] <= 0).any():
                issues.append("Non-positive contract_multiplier detected")

        # 检查结算价与收盘价差异（通常不应太大）
        if "settle" in df.columns and "close" in df.columns:
            close_safe = df["close"].replace(0, float("nan"))
            diff_pct = abs(df["settle"] - df["close"]) / close_safe * 100
            if (diff_pct > 10).any():
                issues.append("Large difference between settle and close price detected")

        return issues
