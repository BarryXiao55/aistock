"""JQData API client wrapper."""

import time

import pandas as pd

from aistock.exceptions import SourceRateLimited, SourceUnavailable


class JQDataClient:
    """JQData API 客户端封装"""

    def __init__(self, config: dict | None = None):
        """
        初始化 JQData 客户端。

        Args:
            config: 配置参数
        """
        self._config = config or {}
        self._token = self._config.get("token", "")
        self._request_timeout = self._config.get("request_timeout", 30)
        self._retry_count = self._config.get("retry_count", 3)
        self._retry_delay = self._config.get("retry_delay", 5)
        self._authenticated = False

    def _get_jqdatasdk(self):
        """延迟导入 jqdatasdk"""
        try:
            import jqdatasdk as jq
            if not self._authenticated:
                if not self._token:
                    raise SourceUnavailable("JQData token not configured")
                jq.auth(self._token)
                self._authenticated = True
            return jq
        except ImportError:
            raise SourceUnavailable("jqdatasdk package not installed. Install with: pip install jqdatasdk")

    def get_stock_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "daily",
        fq: str = "pre",
    ) -> pd.DataFrame:
        """
        获取股票日线数据。

        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 频率 (daily, minute)
            fq: 复权类型 (pre=前复权, post=后复权, None=不复权)

        Returns:
            pd.DataFrame: 日线数据
        """
        jq = self._get_jqdatasdk()

        for attempt in range(self._retry_count):
            try:
                # 获取股票数据
                df = jq.get_price(
                    code,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    fq=fq,
                    fields=["open", "high", "low", "close", "volume", "money"],
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"JQData rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"JQData API error: {e}")

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
        jq = self._get_jqdatasdk()

        for attempt in range(self._retry_count):
            try:
                df = jq.get_price(
                    code,
                    start_date=start_date,
                    end_date=end_date,
                    frequency="daily",
                    fields=["open", "high", "low", "close", "volume", "money"],
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"JQData rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"JQData API error: {e}")

    def get_finance_data(
        self,
        code: str,
        stat_date: str | None = None,
    ) -> pd.DataFrame:
        """
        获取财务数据。

        Args:
            code: 股票代码
            stat_date: 报告期 (可选)

        Returns:
            pd.DataFrame: 财务数据
        """
        jq = self._get_jqdatasdk()

        for attempt in range(self._retry_count):
            try:
                # 获取财务数据
                df = jq.get_fundamentals(
                    jq.query(
                        jq.finance_indicator.code,
                        jq.finance_indicator.pub_date,
                        jq.finance_indicator.net_profit,
                        jq.finance_indicator.roe,
                    ).filter(
                        jq.finance_indicator.code == code
                    ),
                    statDate=stat_date,
                )
                return df
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg:
                    time.sleep(self._retry_delay * (2**attempt))
                    raise SourceRateLimited(f"JQData rate limited: {e}")
                elif attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
                else:
                    raise SourceUnavailable(f"JQData API error: {e}")

    def check_health(self) -> bool:
        """健康检查"""
        try:
            jq = self._get_jqdatasdk()
            # 尝试获取一个简单的数据来验证连通性
            df = jq.get_price(
                "000001.XSHE",
                start_date="2025-01-01",
                end_date="2025-01-01",
                frequency="daily",
            )
            return True
        except Exception:
            return False
