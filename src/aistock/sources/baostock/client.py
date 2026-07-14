"""Baostock API client wrapper."""

import time

import pandas as pd

from aistock.exceptions import SourceUnavailable


class BaoStockClient:
    """Baostock API 客户端封装"""

    def __init__(self, config: dict | None = None):
        self._config = config or {}
        self._bs = None

    def _get_baostock(self):
        """延迟导入 baostock"""
        try:
            import baostock as bs
            if self._bs is None:
                self._bs = bs
                # 登录
                login_result = bs.login()
                if login_result.error_code != '0':
                    raise SourceUnavailable(f"Baostock login failed: {login_result.error_msg}")
            return self._bs
        except ImportError:
            raise SourceUnavailable("baostock package not installed")

    def get_stock_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjustflag: str = "2",
    ) -> pd.DataFrame:
        """
        获取股票日线数据。

        Args:
            code: 股票代码，如 "sh.600000"
            start_date: 开始日期，格式 "YYYY-MM-DD"
            end_date: 结束日期，格式 "YYYY-MM-DD"
            adjustflag: 复权类型 1=后复权 2=前复权 3=不复权
        """
        bs = self._get_baostock()

        # 转换代码格式: "000001.SZ" -> "sz.000001"
        bs_code = self._convert_code(code)

        try:
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag=adjustflag,
            )

            if rs.error_code != '0':
                raise SourceUnavailable(f"Baostock API error: {rs.error_msg}")

            # 转换为 DataFrame
            data_list = []
            while (rs.error_code == '0') and rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 转换数据类型
            numeric_columns = ["open", "high", "low", "close", "volume", "amount", "turn", "pctChg"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            return df

        except Exception as e:
            raise SourceUnavailable(f"Baostock API error: {e}")

    def get_index_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取指数日线数据"""
        bs = self._get_baostock()

        # 指数代码格式: "000001" -> "sh.000001"
        if code.startswith("0") or code.startswith("3"):
            bs_code = f"sh.{code}"
        else:
            bs_code = f"sz.{code}"

        try:
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
            )

            if rs.error_code != '0':
                raise SourceUnavailable(f"Baostock API error: {rs.error_msg}")

            data_list = []
            while (rs.error_code == '0') and rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            numeric_columns = ["open", "high", "low", "close", "volume", "amount"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            return df

        except Exception as e:
            raise SourceUnavailable(f"Baostock API error: {e}")

    def _convert_code(self, code: str) -> str:
        """
        转换股票代码格式。

        输入: "000001.SZ" 或 "600000.SH"
        输出: "sz.000001" 或 "sh.600000"
        """
        if "." in code:
            parts = code.split(".")
            return f"{parts[1].lower()}.{parts[0]}"

        # 根据代码前缀判断
        if code.startswith("6"):
            return f"sh.{code}"
        elif code.startswith(("0", "3")):
            return f"sz.{code}"
        elif code.startswith("8") or code.startswith("4"):
            return f"bj.{code}"
        else:
            return f"sh.{code}"

    def check_health(self) -> bool:
        """健康检查"""
        try:
            bs = self._get_baostock()
            # 尝试获取一个简单的数据来验证连通性
            rs = bs.query_history_k_data_plus(
                "sh.000001",
                "date,close",
                start_date="2025-01-01",
                end_date="2025-01-01",
            )
            return rs.error_code == '0'
        except Exception:
            return False

    def logout(self):
        """登出"""
        if self._bs is not None:
            self._bs.logout()
            self._bs = None
