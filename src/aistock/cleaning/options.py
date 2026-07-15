"""Options specific cleaning step."""

import pandas as pd

from aistock.cleaning.interface import CleaningStep


class OptionsCleaner(CleaningStep):
    """期权特定清洗步骤"""

    name = "options"

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """执行期权特定清洗"""
        # 1. 标记实值/虚值/平值期权
        if all(col in df.columns for col in ["close", "strike_price", "option_type"]):
            strike_safe = df["strike_price"].replace(0, float("nan"))
            # 简化计算：使用收盘价和行权价比较
            if "underlying_price" in df.columns:
                # 有标的价格时精确计算
                df["moneyness"] = df["underlying_price"] / strike_safe
            else:
                # 没有标的价格时使用收盘价近似
                df["moneyness"] = df["close"] / strike_safe

            # 标记期权状态
            df["option_status"] = "at_the_money"  # 平值
            if "option_type" in df.columns:
                # 看涨期权：标的价格 > 行权价 为实值
                call_mask = df["option_type"] == "call"
                df.loc[call_mask & (df["moneyness"] > 1.05), "option_status"] = "in_the_money"
                df.loc[call_mask & (df["moneyness"] < 0.95), "option_status"] = "out_of_the_money"

                # 看跌期权：标的价格 < 行权价 为实值
                put_mask = df["option_type"] == "put"
                df.loc[put_mask & (df["moneyness"] < 0.95), "option_status"] = "in_the_money"
                df.loc[put_mask & (df["moneyness"] > 1.05), "option_status"] = "out_of_the_money"

            status_counts = df["option_status"].value_counts()
            ctx.log.info(f"Option status distribution: {status_counts.to_dict()}")

        # 2. 标记临近到期期权（<7天）
        if "expiry_date" in df.columns:
            from datetime import date, timedelta
            one_week_later = date.today() + timedelta(days=7)
            df["near_expiry"] = pd.to_datetime(df["expiry_date"]).dt.date <= one_week_later
            near_expiry_count = df["near_expiry"].sum()
            if near_expiry_count > 0:
                ctx.log.info(f"Marked {near_expiry_count} near-expiry options")

        # 3. 计算持仓量变化
        if "open_interest" in df.columns and "code" in df.columns:
            if not df.empty and "trade_date" in df.columns:
                df = df.sort_values(["code", "trade_date"])
                df["oi_change"] = df.groupby("code")["open_interest"].diff()
                df["oi_change"] = df["oi_change"].fillna(0)

        # 4. 计算隐含波动率变化
        if "implied_volatility" in df.columns and "code" in df.columns:
            if not df.empty and "trade_date" in df.columns:
                df = df.sort_values(["code", "trade_date"])
                df["iv_change"] = df.groupby("code")["implied_volatility"].diff()
                df["iv_change"] = df["iv_change"].fillna(0)

        return df

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验"""
        issues = []

        # 检查隐含波动率范围
        if "implied_volatility" in df.columns:
            if (df["implied_volatility"] < 0).any() or (df["implied_volatility"] > 500).any():
                issues.append("implied_volatility out of reasonable range")

        # 检查 Delta 范围
        if "delta" in df.columns:
            if (df["delta"] < -1).any() or (df["delta"] > 1).any():
                issues.append("delta out of range (-1 to 1)")

        # 检查行权价
        if "strike_price" in df.columns:
            if (df["strike_price"] <= 0).any():
                issues.append("Non-positive strike_price detected")

        return issues
