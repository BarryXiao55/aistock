"""AkShare futures SourceNode implementation."""

import pandas as pd

from aistock.pipeline.source import SourceNode
from aistock.pipeline.models import FetchSpec
from aistock.schemas.futures import FuturesSchema
from aistock.sources.akstock_futures.client import AkStockFuturesClient
from aistock.sources.akstock_futures.mapper import map_futures_columns, parse_futures_code


class AkStockFuturesSource(SourceNode):
    """AkShare 期货数据源实现"""

    name = "akstock_futures"

    def __init__(self, config: dict | None = None):
        super().__init__()
        self._config = config or {}
        self._client = AkStockFuturesClient(self._config)

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

        # 确定要下载的合约列表
        codes = spec.codes or self._get_all_codes(spec.asset_type)

        for code in codes:
            try:
                # 解析合约代码
                code_info = parse_futures_code(code)

                # 调用 API
                df = self._client.get_futures_daily(
                    symbol=code,
                    start_date=spec.start_date.strftime("%Y%m%d"),
                    end_date=spec.end_date.strftime("%Y%m%d"),
                )

                if df is not None and not df.empty:
                    # 映射列名
                    df = map_futures_columns(df)

                    # 添加合约信息
                    df["code"] = code
                    df["underlying"] = code_info["underlying"]
                    df["delivery_month"] = code_info["delivery_month"]
                    if code_info["expiry_date"]:
                        df["expiry_date"] = code_info["expiry_date"]

                    # 根据合约代码推断交易所
                    df["exchange"] = self._infer_exchange(code_info["underlying"])

                    all_dfs.append(df)

            except Exception as e:
                print(f"Failed to fetch futures {code}: {e}")
                continue

        if not all_dfs:
            return pd.DataFrame()

        return pd.concat(all_dfs, ignore_index=True)

    def _infer_exchange(self, underlying: str) -> str:
        """根据标的物推断交易所"""
        # 主要期货品种的交易所映射
        exchange_map = {
            # 中金所 (CFFEX)
            "IF": "CFFEX",  # 沪深300股指期货
            "IH": "CFFEX",  # 上证50股指期货
            "IC": "CFFEX",  # 中证500股指期货
            "IM": "CFFEX",  # 中证1000股指期货
            "T": "CFFEX",   # 10年期国债期货
            "TF": "CFFEX",  # 5年期国债期货
            "TS": "CFFEX",  # 2年期国债期货

            # 上期所 (SHFE)
            "CU": "SHFE",  # 铜
            "AL": "SHFE",  # 铝
            "ZN": "SHFE",  # 锌
            "PB": "SHFE",  # 铅
            "NI": "SHFE",  # 镍
            "SN": "SHFE",  # 锡
            "AU": "SHFE",  # 黄金
            "AG": "SHFE",  # 白银
            "RB": "SHFE",  # 螺纹钢
            "WR": "SHFE",  # 线材
            "HC": "SHFE",  # 热轧卷板
            "SS": "SHFE",  # 不锈钢
            "BU": "SHFE",  # 沥青
            "RU": "SHFE",  # 橡胶
            "FU": "SHFE",  # 燃料油
            "SP": "SHFE",  # 纸浆

            # 大商所 (DCE)
            "A": "DCE",    # 豆一
            "B": "DCE",    # 豆二
            "M": "DCE",    # 豆粕
            "Y": "DCE",    # 豆油
            "P": "DCE",    # 棕榈油
            "C": "DCE",    # 玉米
            "CS": "DCE",   # 玉米淀粉
            "JD": "DCE",   # 鸡蛋
            "L": "DCE",    # 聚乙烯
            "V": "DCE",    # 聚氯乙烯
            "PP": "DCE",   # 聚丙烯
            "EB": "DCE",   # 苯乙烯
            "EG": "DCE",   # 乙二醇
            "J": "DCE",    # 焦炭
            "JM": "DCE",   # 焦煤
            "I": "DCE",    # 铁矿石

            # 郑商所 (CZCE)
            "SR": "CZCE",  # 白糖
            "CF": "CZCE",  # 棉花
            "ZC": "CZCE",  # 动力煤
            "TA": "CZCE",  # PTA
            "MA": "CZCE",  # 甲醇
            "FG": "CZCE",  # 玻璃
            "RM": "CZCE",  # 菜粕
            "OI": "CZCE",  # 菜油
            "AP": "CZCE",  # 苹果
            "CJ": "CZCE",  # 红枣
            "UR": "CZCE",  # 尿素
            "SA": "CZCE",  # 纯碱
        }

        return exchange_map.get(underlying, "UNKNOWN")

    def _get_all_codes(self, asset_type: str) -> list[str]:
        """获取指定资产类型的所有代码"""
        return []

    def check_health(self) -> bool:
        """健康检查"""
        return self._client.check_health()
