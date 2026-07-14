"""AkShare options API client wrapper."""

import time

import pandas as pd

from aistock.exceptions import SourceRateLimited, SourceUnavailable


class AkStockOptionsClient:
    """AkShare 期权 API 客户端封装"""

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

    def get_options_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取期权日线数据"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                # 使用期权日线接口
                df = ak.option_sse_daily(symbol=symbol)
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

    def get_options_info(self) -> pd.DataFrame:
        """获取期权合约信息"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                df = ak.option_sse_list_sina(symbol="50ETF")
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
            # 尝试获取期权合约列表
            df = ak.option_sse_list_sina(symbol="50ETF")
            return df is not None and not df.empty
        except Exception:
            return False
