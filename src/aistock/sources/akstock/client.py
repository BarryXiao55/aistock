"""AkShare API client wrapper."""

import time
from typing import Any

import pandas as pd

from aistock.exceptions import SourceRateLimited, SourceUnavailable


class AkStockClient:
    """AkShare API 客户端封装"""

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._request_timeout = self._config.get("request_timeout", 30)
        self._retry_count = self._config.get("retry_count", 3)
        self._retry_delay = self._config.get("retry_delay", 5)

    def _get_akshare(self):
        """延迟导入 akshare"""
        try:
            import akshare as ak
            return ak
        except ImportError:
            raise SourceUnavailable("akshare package not installed")

    def get_stock_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """获取股票日线数据"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                # akshare 使用不同的接口名称
                # 股票日线: stock_zh_a_hist
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"AkShare rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"AkShare API error: {e}")

    def get_index_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取指数日线数据 (东方财富 API，支持日期过滤)"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                df = ak.stock_zh_index_daily_em(
                    symbol=f"sh{code}",
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"AkShare rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"AkShare API error: {e}")

    def get_etf_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取 ETF 日线数据 (东方财富 API，支持日期过滤)"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                df = ak.fund_etf_hist_em(
                    symbol=code,
                    period="daily",
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"AkShare rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"AkShare API error: {e}")

    def get_finance_data(self, code: str) -> pd.DataFrame:
        """获取财务数据"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                df = ak.stock_financial_abstract_ths(symbol=code)
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"AkShare rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"AkShare API error: {e}")

    def get_north_flow(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取北向资金数据"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                df = ak.stock_hsgt_north_net_flow_in_em()
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"AkShare rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"AkShare API error: {e}")

    def check_health(self) -> bool:
        """健康检查"""
        try:
            ak = self._get_akshare()
            # 尝试获取一个简单的数据来验证连通性
            ak.stock_zh_a_spot_em()
            return True
        except Exception:
            return False
