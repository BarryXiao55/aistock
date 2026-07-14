"""AkShare SourceNode implementation."""

import pandas as pd

from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.minute import StockMinuteSchema
from aistock.schemas.finance import FinanceSchema
from aistock.sources.akstock.client import AkStockClient
from aistock.sources.akstock.mapper import map_daily_columns, unify_code


class AkStockSource(SourceNode):
    """AkShare 数据源实现"""

    name = "akstock"

    def __init__(self, config: dict | None = None):
        super().__init__()
        self._config = config or {}
        self._client = AkStockClient(self._config)

    def supports(self, asset_type: str, schema: type) -> bool:
        """声明支持的数据类型"""
        supported_schemas = {
            StockDailySchema,
            StockMinuteSchema,
            FinanceSchema,
        }
        supported_asset_types = {"stock", "index", "etf"}
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

        # 确定要下载的代码列表
        codes = spec.codes or self._get_all_codes(spec.asset_type)

        for code in codes:
            try:
                # 统一代码格式
                raw_code = code.split(".")[0] if "." in code else code

                # 调用 API
                df = self._client.get_stock_daily(
                    code=raw_code,
                    start_date=spec.start_date.strftime("%Y%m%d"),
                    end_date=spec.end_date.strftime("%Y%m%d"),
                )

                if df is not None and not df.empty:
                    # 映射列名
                    df = map_daily_columns(df)

                    # 添加代码列
                    df["code"] = unify_code(raw_code)

                    all_dfs.append(df)

            except Exception as e:
                # 记录错误但继续处理其他代码
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
                raw_code = code.split(".")[0] if "." in code else code
                df = self._client.get_finance_data(raw_code)

                if df is not None and not df.empty:
                    df["code"] = unify_code(raw_code)
                    all_dfs.append(df)

            except Exception as e:
                print(f"Failed to fetch finance for {code}: {e}")
                continue

        if not all_dfs:
            return pd.DataFrame()

        return pd.concat(all_dfs, ignore_index=True)

    def _get_all_codes(self, asset_type: str) -> list[str]:
        """获取指定资产类型的所有代码"""
        # 实际实现中应该从配置或外部数据源获取
        # 这里返回空列表，由调用方指定 codes
        return []

    def check_health(self) -> bool:
        """健康检查"""
        return self._client.check_health()
