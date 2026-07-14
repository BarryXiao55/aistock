"""JQData SourceNode implementation."""

import pandas as pd

from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.schemas.daily import StockDailySchema
from aistock.schemas.finance import FinanceSchema
from aistock.sources.jqdata.client import JQDataClient
from aistock.sources.jqdata.mapper import map_daily_columns, unify_code, to_jqcode


class JQDataSource(SourceNode):
    """JQData 数据源实现"""

    name = "jqdata"

    def __init__(self, config: dict | None = None):
        """
        初始化 JQData 数据源。

        Args:
            config: 配置参数
        """
        super().__init__()
        self._config = config or {}
        self._client = JQDataClient(self._config)

    def supports(self, asset_type: str, schema: type) -> bool:
        """声明支持的数据类型"""
        return asset_type in ["stock", "index"] and schema in [StockDailySchema, FinanceSchema]

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
                # 转换代码格式
                jq_code = to_jqcode(code)

                # 调用 API
                df = self._client.get_stock_daily(
                    code=jq_code,
                    start_date=spec.start_date.strftime("%Y-%m-%d"),
                    end_date=spec.end_date.strftime("%Y-%m-%d"),
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
                jq_code = to_jqcode(code)

                df = self._client.get_finance_data(jq_code)

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
        # 实际实现中应该从配置或外部数据源获取
        return []

    def check_health(self) -> bool:
        """健康检查"""
        return self._client.check_health()
