"""AkShare convertible bond SourceNode implementation."""

import pandas as pd

from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.schemas.convertible_bond import ConvertibleBondSchema
from aistock.sources.akstock_cb.client import AkStockCBClient
from aistock.sources.akstock_cb.mapper import map_cb_columns, unify_cb_code


class AkStockCBSource(SourceNode):
    """AkShare 可转债数据源实现"""

    name = "akstock_cb"

    def __init__(self, config: dict | None = None):
        super().__init__()
        self._config = config or {}
        self._client = AkStockCBClient(self._config)

    def supports(self, asset_type: str, schema: type) -> bool:
        """声明支持的数据类型"""
        return asset_type == "cb" and schema == ConvertibleBondSchema

    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        """执行数据下载"""
        if spec.schema is ConvertibleBondSchema:
            return self._fetch_cb(spec)
        else:
            raise ValueError(f"Unsupported schema: {spec.schema}")

    def _fetch_cb(self, spec: FetchSpec) -> pd.DataFrame:
        """下载可转债数据"""
        try:
            # 获取可转债列表
            df = self._client.get_cb_daily(
                code="",
                start_date=spec.start_date.strftime("%Y%m%d"),
                end_date=spec.end_date.strftime("%Y%m%d"),
            )

            if df is None or df.empty:
                return pd.DataFrame()

            # 映射列名
            df = map_cb_columns(df)

            # 如果指定了代码，过滤数据
            if spec.codes:
                codes = [unify_cb_code(c) for c in spec.codes]
                df = df[df["code"].isin(codes)]

            # 添加 trade_date 列（使用当前日期作为默认值）
            if "trade_date" not in df.columns:
                df["trade_date"] = pd.Timestamp.now().date()

            return df

        except Exception as e:
            raise Exception(f"Failed to fetch convertible bond data: {e}")

    def check_health(self) -> bool:
        """健康检查"""
        return self._client.check_health()
