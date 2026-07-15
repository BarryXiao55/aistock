"""Tushare options SourceNode implementation."""

import pandas as pd

from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.schemas.options import OptionsSchema
from aistock.sources.tushare_options.client import TuShareOptionsClient
from aistock.sources.tushare_options.mapper import map_options_columns, unify_option_code


class TuShareOptionsSource(SourceNode):
    """Tushare 期权数据源实现"""

    name = "tushare_options"

    def __init__(self, config: dict | None = None):
        super().__init__()
        self._config = config or {}
        self._client = TuShareOptionsClient(self._config)

    def supports(self, asset_type: str, schema: type) -> bool:
        """声明支持的数据类型"""
        return asset_type == "option" and schema == OptionsSchema

    def fetch(self, spec: FetchSpec) -> pd.DataFrame:
        """执行数据下载"""
        if spec.schema is OptionsSchema:
            return self._fetch_options(spec)
        else:
            raise ValueError(f"Unsupported schema: {spec.schema}")

    def _fetch_options(self, spec: FetchSpec) -> pd.DataFrame:
        """下载期权数据"""
        all_dfs = []

        codes = spec.codes or self._get_all_codes(spec.asset_type)

        for code in codes:
            try:
                # 转换代码格式 - 根据期权代码推断交易所
                ts_code = self._map_exchange(code)

                # 调用 API
                df = self._client.get_options_daily(
                    ts_code=ts_code,
                    start_date=spec.start_date.strftime("%Y%m%d"),
                    end_date=spec.end_date.strftime("%Y%m%d"),
                )

                if df is not None and not df.empty:
                    # 映射列名
                    df = map_options_columns(df)

                    # 添加代码列
                    df["code"] = unify_option_code(code)

                    # 解析期权信息
                    from aistock.sources.akstock_options.mapper import parse_option_code
                    code_info = parse_option_code(code)
                    df["underlying"] = code_info["underlying"]
                    df["option_type"] = code_info["option_type"]
                    df["strike_price"] = code_info["strike_price"]
                    if code_info["expiry_date"]:
                        df["expiry_date"] = code_info["expiry_date"]

                    all_dfs.append(df)

            except Exception as e:
                self.ctx.log.warning(f"Failed to fetch options {code}: {e}")
                continue

        if not all_dfs:
            return pd.DataFrame()

        return pd.concat(all_dfs, ignore_index=True)

    def _get_all_codes(self, asset_type: str) -> list[str]:
        """获取指定资产类型的所有代码"""
        return []

    @staticmethod
    def _map_exchange(code: str) -> str:
        """根据期权代码推断交易所后缀

        Tushare 期权格式: 10005867.SSE (上交所), 90003688.SZSE (深交所)
        """
        # 已经带后缀的直接返回
        if "." in code:
            return code

        # 8位数字期权代码: 上交所 10xxxxxx, 深交所 9xxxxxxx
        if code.startswith("10") and len(code) == 8:
            return f"{code}.SSE"
        elif code.startswith("9") and len(code) == 8:
            return f"{code}.SZSE"
        else:
            return f"{code}.SSE"  # 默认上交所

    def check_health(self) -> bool:
        """健康检查"""
        return self._client.check_health()
