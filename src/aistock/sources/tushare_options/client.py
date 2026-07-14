"""Tushare options API client wrapper."""

import time

import pandas as pd

from aistock.exceptions import SourceRateLimited, SourceUnavailable


class TuShareOptionsClient:
    """Tushare 期权 API 客户端封装"""

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

    def get_options_daily(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取期权日线数据"""
        ts_api = self._get_tushare()

        try:
            time.sleep(self._request_interval)

            df = ts_api.opt_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                return pd.DataFrame()

            return df

        except Exception as e:
            error_msg = str(e).lower()
            if "exceed" in error_msg or "limit" in error_msg:
                raise SourceRateLimited(f"Tushare rate limited: {e}")
            raise SourceUnavailable(f"Tushare API error: {e}")

    def get_options_basic(self) -> pd.DataFrame:
        """获取期权合约基本信息"""
        ts_api = self._get_tushare()

        try:
            time.sleep(self._request_interval)

            df = ts_api.opt_basic(exchange="", fields="ts_code,name,call_put,exercise_price,deliver_date,list_date,delist_date")

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
            # 尝试获取期权合约列表
            df = ts_api.opt_basic(exchange="", fields="ts_code")
            return df is not None and not df.empty
        except Exception:
            return False
