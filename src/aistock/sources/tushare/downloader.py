"""Tushare SourceNode implementation."""

import pandas as pd

from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.finance import FinanceSchema
from aistock.sources.tushare.client import TuShareClient
from aistock.sources.tushare.mapper import map_daily_columns, unify_code


class TuShareSource(SourceNode):
    """Tushare 数据源实现"""

    name = "tushare"

    def __init__(self, config: dict | None = None):
        super().__init__()
        self._config = config or {}
        self._client = TuShareClient(self._config)

    def supports(self, asset_type: str, schema: type) -> bool:
        """声明支持的数据类型"""
        supported_schemas = {StockDailySchema, FinanceSchema}
        supported_asset_types = {"stock", "index"}
        return asset_type in supported_asset_types and schema in supported_schemas

    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        """执行数据下载"""
        if spec.schema is StockDailySchema:
            return self._fetch_daily(spec)
        elif spec.schema is FinanceSchema:
            return self._fetch_finance(spec)
        else:
            raise ValueError(f"Unsupported schema: {spec.schema}")

    def _fetch_daily(self, spec: FetchSpec) -> pd.DataFrame:
        """下载日线数据"""
        all_dfs = []

        codes = spec.codes or self._get_all_codes(spec.asset_type)

        for code in codes:
            try:
                # 调用 API
                df = self._client.get_stock_daily(
                    code=code,
                    start_date=spec.start_date.strftime("%Y%m%d"),
                    end_date=spec.end_date.strftime("%Y%m%d"),
                )

                if df is not None and not df.empty:
                    # 映射列名
                    df = map_daily_columns(df)

                    # 添加代码列
                    df["code"] = unify_code(code)

                    all_dfs.append(df)

            except Exception as e:
                print(f"Failed to fetch {code}: {e}")
                continue

        if not all_dfs:
            return pd.DataFrame()

        return pd.concat(all_dfs, ignore_index=True)

    def _fetch_finance(self, spec: FetchSpec) -> pd.DataFrame:
        """下载财务数据"""
        all_dfs = []

        codes = spec.codes or self._get_all_codes(spec.asset_type)

        for code in codes:
            try:
                df = self._client.get_finance_data(code)

                if df is not None and not df.empty:
                    df["code"] = unify_code(code)
                    all_dfs.append(df)

            except Exception as e:
                print(f"Failed to fetch finance for {code}: {e}")
                continue

        if not all_dfs:
            return pd.DataFrame()

        return pd.concat(all_dfs, ignore_index=True)

    def _get_all_codes(self, asset_type: str) -> list[str]:
        """获取指定资产类型的所有代码"""
        return []

    def check_health(self) -> bool:
        """健康检查"""
        return self._client.check_health()
