"""Universal cleaning step --- dedup, null handling, code format unification."""

import pandas as pd

from aistock.cleaning.interface import CleaningStep


class UniversalCleaner(CleaningStep):
    """通用清洗步骤：去重、空值处理、代码格式统一"""

    name = "universal"

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """执行通用清洗"""
        initial_count = len(df)

        # 1. 去重
        df = df.drop_duplicates()
        removed_dups = initial_count - len(df)

        # 2. 空值处理：关键字段不能为空
        critical_columns = ["code", "trade_date"]
        if all(col in df.columns for col in critical_columns):
            before_null = len(df)
            df = df.dropna(subset=critical_columns)
            removed_null = before_null - len(df)
        else:
            removed_null = 0

        # 3. 代码格式统一：000001 -> 000001.SZ
        if "code" in df.columns:
            df["code"] = df["code"].apply(self._unify_code_format)

        # 记录清洗结果
        if removed_dups > 0:
            ctx.log.info(f"Removed {removed_dups} duplicate rows")
        if removed_null > 0:
            ctx.log.info(f"Removed {removed_null} rows with null critical fields")

        return df

    @staticmethod
    def _unify_code_format(code: str) -> str:
        """统一代码格式：添加交易所后缀"""
        if pd.isna(code) or not isinstance(code, str):
            return code

        # 已经有后缀的直接返回
        if "." in code:
            return code

        # 根据代码前缀判断交易所
        if code.startswith("6"):
            return f"{code}.SH"
        elif code.startswith(("0", "3")):
            return f"{code}.SZ"
        elif code.startswith("8") or code.startswith("4"):
            return f"{code}.BJ"
        else:
            # 默认沪市
            return f"{code}.SH"
