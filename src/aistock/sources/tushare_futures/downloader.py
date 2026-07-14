"""Tushare futures SourceNode implementation."""

import pandas as pd

from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.schemas.futures import FuturesSchema
from aistock.sources.tushare_futures.client import TuShareFuturesClient
from aistock.sources.tushare_futures.mapper import map_futures_columns, unify_futures_code


class TuShareFuturesSource(SourceNode):
    """Tushare 期货数据源实现"""

    name = "tushare_futures"

    def __init__(self, config: dict | None = None):
        super().__init__()
        self._config = config or {}
        self._client = TuShareFuturesClient(self._config)

    def supports(self, asset_type: str, schema: type) -> bool:
        """声明支持的数据类型"""
        return asset_type == "future" and schema == FuturesSchema

    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        """执行数据下载"""
        if spec.schema is FuturesSchema:
            return self._fetch_futures(spec)
        else:
            raise ValueError(f"Unsupported schema: {spec.schema}")

    def _fetch_futures(self, spec: FetchSpec) -> pd.DataFrame:
        """下载期货数据"""
        all_dfs = []

        codes = spec.codes or self._get_all_codes(spec.asset_type)

        for code in codes:
            try:
                # 转换代码格式
                ts_code = f"{code}.UNKNOWN"  # Tushare 需要交易所后缀

                # 调用 API
                df = self._client.get_futures_daily(
                    ts_code=ts_code,
                    start_date=spec.start_date.strftime("%Y%m%d"),
                    end_date=spec.end_date.strftime("%Y%m%d"),
                )

                if df is not None and not df.empty:
                    # 映射列名
                    df = map_futures_columns(df)

                    # 添加代码列
                    df["code"] = unify_futures_code(code)

                    # 解析合约信息
                    from aistock.sources.akstock_futures.mapper import parse_futures_code
                    code_info = parse_futures_code(code)
                    df["underlying"] = code_info["underlying"]
                    df["delivery_month"] = code_info["delivery_month"]
                    if code_info["expiry_date"]:
                        df["expiry_date"] = code_info["expiry_date"]

                    all_dfs.append(df)

            except Exception as e:
                print(f"Failed to fetch futures {code}: {e}")
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
