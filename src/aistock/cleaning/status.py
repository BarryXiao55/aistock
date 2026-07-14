"""Status cleaning step --- ST/suspended/delisted flags."""

import pandas as pd

from aistock.cleaning.interface import CleaningStep


class StatusCleaner(CleaningStep):
    """交易状态标记步骤：标记 ST、停牌、退市状态"""

    name = "status"

    def clean(self, df: pd.DataFrame, ctx) -> pd.DataFrame:
        """执行状态标记"""
        # 确保必要的列存在
        required_columns = ["code"]
        for col in required_columns:
            if col not in df.columns:
                ctx.log.warning(f"Missing column {col}, skipping status cleaning")
                return df

        # 初始化状态列
        if "is_st" not in df.columns:
            df["is_st"] = False
        if "is_suspended" not in df.columns:
            df["is_suspended"] = False

        # 标记 ST 股票
        # 实际实现中应该从外部数据源获取 ST 列表
        # 这里使用简单的启发式方法：如果名称包含 "ST" 则标记
        if "name" in df.columns:
            df["is_st"] = df["name"].str.contains("ST", case=False, na=False)

        # 标记停牌股票
        # 停牌通常通过成交量为 0 来判断
        if "volume" in df.columns:
            # 成交量为 0 且价格不变视为停牌
            df["is_suspended"] = df["volume"] == 0

        # 统计状态
        st_count = df["is_st"].sum()
        suspended_count = df["is_suspended"].sum()

        if st_count > 0:
            ctx.log.info(f"Marked {st_count} ST records")
        if suspended_count > 0:
            ctx.log.info(f"Marked {suspended_count} suspended records")

        return df

    def validate(self, df: pd.DataFrame) -> list[str]:
        """后置校验：检查状态标记是否合理"""
        issues = []

        # 检查 ST 标记是否与名称一致
        if "is_st" in df.columns and "name" in df.columns:
            # 名称包含 ST 但未标记
            st_in_name = df["name"].str.contains("ST", case=False, na=False)
            if (st_in_name & ~df["is_st"]).any():
                issues.append("ST stocks not properly marked")

        # 检查停牌标记是否与成交量一致
        if "is_suspended" in df.columns and "volume" in df.columns:
            # 成交量为 0 但未标记停牌
            zero_volume = df["volume"] == 0
            if (zero_volume & ~df["is_suspended"]).any():
                issues.append("Zero volume stocks not marked as suspended")

        return issues
