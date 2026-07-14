"""Mootdx API client wrapper."""

import time

import pandas as pd

from aistock.exceptions import SourceRateLimited, SourceUnavailable


class MootdxClient:
    """Mootdx API 客户端封装"""

    def __init__(self, config: dict | None = None):
        """
        初始化 Mootdx 客户端。

        Args:
            config: 配置参数
        """
        self._config = config or {}
        self._request_timeout = self._config.get("request_timeout", 30)
        self._retry_count = self._config.get("retry_count", 3)
        self._retry_delay = self._config.get("retry_delay", 5)
        self._client = None

    def _get_mootdx(self):
        """延迟导入 mootdx"""
        try:
            from mootdx.quotes import Quotes
            if self._client is None:
                self._client = Quotes.factory(market="std")
            return self._client
        except ImportError:
            raise SourceUnavailable("mootdx package not installed. Install with: pip install mootdx")

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
        client = self._get_mootdx()

        for attempt in range(self._retry_count):
            try:
                # 转换代码格式: "000001.SZ" -> "000001"
                symbol = code.split(".")[0] if "." in code else code

                # 获取日线数据
                df = client.bars(
                    symbol=symbol,
                    frequency=9,  # 9 = 日线
                    offset=0,
                    start=start_date.replace("-", ""),
                    end=end_date.replace("-", ""),
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"Mootdx rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"Mootdx API error: {e}")

    def get_stock_info(self, code: str) -> pd.DataFrame:
        """
        获取股票基本信息。

        Args:
            code: 股票代码

        Returns:
            pd.DataFrame: 股票基本信息
        """
        client = self._get_mootdx()

        for attempt in range(self._retry_count):
            try:
                symbol = code.split(".")[0] if "." in code else code
                df = client.stocks(symbol=symbol)
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"Mootdx rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"Mootdx API error: {e}")

    def get_index_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        获取指数日线数据。

        Args:
            code: 指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 指数日线数据
        """
        client = self._get_mootdx()

        for attempt in range(self._retry_count):
            try:
                symbol = code.split(".")[0] if "." in code else code
                df = client.bars(
                    symbol=symbol,
                    frequency=9,
                    offset=0,
                    start=start_date.replace("-", ""),
                    end=end_date.replace("-", ""),
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"Mootdx rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"Mootdx API error: {e}")

    def check_health(self) -> bool:
        """健康检查"""
        try:
            client = self._get_mootdx()
            # 尝试获取一个简单的数据来验证连通性
            df = client.bars(symbol="000001", frequency=9, offset=0)
            return df is not None and not df.empty
        except Exception:
            return False
