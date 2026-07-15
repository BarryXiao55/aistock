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
                # 转换代码格式 - 根据合约代码推断交易所
                ts_code = self._map_exchange(code)

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
                self.ctx.log.warning(f"Failed to fetch futures {code}: {e}")
                continue

        if not all_dfs:
            return pd.DataFrame()

        return pd.concat(all_dfs, ignore_index=True)

    def _get_all_codes(self, asset_type: str) -> list[str]:
        """获取指定资产类型的所有代码"""
        return []

    @staticmethod
    def _map_exchange(code: str) -> str:
        """根据合约代码推断交易所后缀

        Tushare 期货格式: IF2501.CFE, cu2501.SHF, m2501.DCE, SR501.CZC
        """
        # 已经带后缀的直接返回
        if "." in code:
            parts = code.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                return code

        # 根据合约代码前缀推断交易所
        prefix = code.rstrip("0123456789").lower() if code else ""

        exchange_map = {
            # CFFEX (中金所)
            "if": "CFE", "ic": "CFE", "ih": "CFE", "im": "CFE", "tf": "CFE", "t": "CFE", "ts": "CFE",
            # SHFE (上期所)
            "cu": "SHF", "al": "SHF", "zn": "SHF", "pb": "SHF", "ni": "SHF", "sn": "SHF",
            "au": "SHF", "ag": "SHF", "rb": "SHF", "hc": "SHF", "ss": "SHF", "bu": "SHF",
            "ru": "SHF", "fu": "SHF", "sp": "SHF", "nr": "SHF", "lu": "SHF", "bc": "SHF",
            # DCE (大商所)
            "m": "DCE", "y": "DCE", "p": "DCE", "c": "DCE", "cs": "DCE", "a": "DCE",
            "b": "DCE", "jd": "DCE", "l": "DCE", "v": "DCE", "pp": "DCE", "j": "DCE",
            "jm": "DCE", "i": "DCE", "eg": "DCE", "eb": "DCE", "pg": "DCE", "lh": "DCE",
            # CZC (郑商所)
            "sr": "CZC", "cf": "CZC", "ta": "CZC", "ma": "CZC", "oi": "CZC", "rm": "CZC",
            "fg": "CZC", "sa": "CZC", "ur": "CZC", "ap": "CZC", "cj": "CZC", "pf": "CZC",
            "pk": "CZC", "sh": "CZC", "si": "CZC",
            # INE (上期能源)
            "sc": "INE", "lu": "INE", "nr": "INE", "bc": "INE",
        }

        exchange = exchange_map.get(prefix, "SHF")  # 默认上期所
        return f"{code}.{exchange}"

    def check_health(self) -> bool:
        """健康检查"""
        return self._client.check_health()
