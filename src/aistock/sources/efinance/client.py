"""EFinance API client wrapper."""

import time

import pandas as pd

from aistock.exceptions import SourceRateLimited, SourceUnavailable


class EFinanceClient:
    """EFinance API 客户端封装"""

    def __init__(self, config: dict | None = None):
        """
        初始化 EFinance 客户端。

        Args:
            config: 配置参数
        """
        self._config = config or {}
        self._request_timeout = self._config.get("request_timeout", 30)
        self._retry_count = self._config.get("retry_count", 3)
        self._retry_delay = self._config.get("retry_delay", 5)

    def _get_efinance(self):
        """延迟导入 efinance"""
        try:
            import efinance as ef
            return ef
        except ImportError:
            raise SourceUnavailable("efinance package not installed. Install with: pip install efinance")

    def get_stock_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        获取股票日线数据。

        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 日线数据
        """
        ef = self._get_efinance()

        for attempt in range(self._retry_count):
            try:
                # 获取股票日线数据
                df = ef.stock.get_quote_history(
                    code,
                    beg=start_date.replace("-", ""),
                    end=end_date.replace("-", ""),
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"EFinance rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"EFinance API error: {e}")

    def get_stock_realtime(self, codes: list[str]) -> pd.DataFrame:
        """
        获取股票实时行情。

        Args:
            codes: 股票代码列表

        Returns:
            pd.DataFrame: 实时行情数据
        """
        ef = self._get_efinance()

        for attempt in range(self._retry_count):
            try:
                df = ef.stock.get_realtime_quotes(codes)
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"EFinance rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"EFinance API error: {e}")

    def get_fund_nav(self, code: str) -> pd.DataFrame:
        """
        获取基金净值数据。

        Args:
            code: 基金代码

        Returns:
            pd.DataFrame: 基金净值数据
        """
        ef = self._get_efinance()

        for attempt in range(self._retry_count):
            try:
                df = ef.fund.get_fund_nav(code)
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"EFinance rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"EFinance API error: {e}")

    def get_futures_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        获取期货日线数据。

        Args:
            code: 期货合约代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 期货日线数据
        """
        ef = self._get_efinance()

        for attempt in range(self._retry_count):
            try:
                df = ef.futures.get_quote_history(
                    code,
                    beg=start_date.replace("-", ""),
                    end=end_date.replace("-", ""),
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"EFinance rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"EFinance API error: {e}")

    def check_health(self) -> bool:
        """健康检查"""
        try:
            ef = self._get_efinance()
            # 尝试获取一个简单的数据来验证连通性
            df = ef.stock.get_realtime_quotes(["000001"])
            return df is not None and not df.empty
        except Exception:
            return False
