"""AkShare futures API client wrapper."""

import time

import pandas as pd

from aistock.exceptions import SourceRateLimited, SourceUnavailable


class AkStockFuturesClient:
    """AkShare 期货 API 客户端封装"""

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

    def get_futures_daily(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取期货日线数据"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                # 使用期货日线接口
                df = ak.futures_zh_daily_sina(symbol=symbol)
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

    def get_futures_info(self) -> pd.DataFrame:
        """获取期货合约信息"""
        ak = self._get_akshare()

        for attempt in range(self._retry_count):
            try:
                df = ak.futures_display_main_sina()
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
            # 尝试获取期货合约列表
            df = ak.futures_display_main_sina()
            return df is not None and not df.empty
        except Exception:
            return False
