"""Tushare API client wrapper."""

import time

import pandas as pd

from aistock.exceptions import SourceUnavailable, SourceRateLimited


class TuShareClient:
    """Tushare API 客户端封装"""

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._token = self._config.get("token", "")
        self._ts = None
        self._request_interval = self._config.get("request_interval", 0.5)

    def _get_tushare(self):
        """延迟导入 tushare"""
        try:
            import tushare as ts
            if self._ts is None:
                if not self._token:
                    raise SourceUnavailable("Tushare token not configured")
                ts.set_token(self._token)
                self._ts = ts.pro_api()
            return self._ts
        except ImportError:
            raise SourceUnavailable("tushare package not installed")

    def get_stock_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adj: str = "qfq",
    ) -> pd.DataFrame:
        """
        获取股票日线数据。

        Args:
            code: 股票代码，如 "000001.SZ"
            start_date: 开始日期，格式 "YYYYMMDD"
            end_date: 结束日期，格式 "YYYYMMDD"
            adj: 复权类型 qfq=前复权 hfq=后复权 None=不复权
        """
        ts_api = self._get_tushare()

        # 转换代码格式: "000001.SZ" -> "000001.SZ" (Tushare 使用相同格式)
        ts_code = code

        try:
            # 限制请求频率
            time.sleep(self._request_interval)

            df = ts_api.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                return pd.DataFrame()

            # 列名已经是英文，无需映射
            # 添加 asset_type 列
            df["asset_type"] = "stock"

            return df

        except Exception as e:
            error_msg = str(e).lower()
            if "exceed" in error_msg or "limit" in error_msg or "频率" in error_msg:
                raise SourceRateLimited(f"Tushare rate limited: {e}")
            raise SourceUnavailable(f"Tushare API error: {e}")

    def get_index_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取指数日线数据"""
        ts_api = self._get_tushare()

        # 指数代码格式: "000001.SH"
        if "." not in code:
            if code.startswith("0") or code.startswith("3"):
                ts_code = f"{code}.SH"
            else:
                ts_code = f"{code}.SZ"
        else:
            ts_code = code

        try:
            time.sleep(self._request_interval)

            df = ts_api.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                return pd.DataFrame()

            df["asset_type"] = "index"
            return df

        except Exception as e:
            error_msg = str(e).lower()
            if "exceed" in error_msg or "limit" in error_msg:
                raise SourceRateLimited(f"Tushare rate limited: {e}")
            raise SourceUnavailable(f"Tushare API error: {e}")

    def get_finance_data(self, code: str) -> pd.DataFrame:
        """获取财务数据"""
        ts_api = self._get_tushare()

        ts_code = code

        try:
            time.sleep(self._request_interval)

            # 获取利润表
            df = ts_api.fina_indicator(ts_code=ts_code)

            if df is None or df.empty:
                return pd.DataFrame()

            return df

        except Exception as e:
            error_msg = str(e).lower()
            if "exceed" in error_msg or "limit" in error_msg:
                raise SourceRateLimited(f"Tushare rate limited: {e}")
            raise SourceUnavailable(f"Tushare API error: {e}")

    def check_health(self) -> bool:
        """健康检查"""
        try:
            ts_api = self._get_tushare()
            # 尝试获取一个简单的数据来验证连通性
            df = ts_api.trade_cal(exchange='SSE', start_date='20250101', end_date='20250101')
            return df is not None and not df.empty
        except Exception:
            return False
