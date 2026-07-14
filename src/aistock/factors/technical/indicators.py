"""Technical indicators factors calculation."""

import numpy as np
import pandas as pd

from aistock.factors.interface import (
    FactorCalculator, FactorMetadata, FactorResult,
    FactorCategory, FactorFrequency,
)


class RSIFactor(FactorCalculator):
    """RSI (Relative Strength Index) 因子"""

    def __init__(self, window: int = 14):
        """
        初始化 RSI 因子。

        Args:
            window: RSI 计算窗口
        """
        self.window = window

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name=f"rsi_{self.window}",
            description=f"{self.window}日相对强弱指标 (RSI)",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["momentum", "oscillator", "rsi"],
            data_requirements=["close"],
            parameters={"window": self.window},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 RSI"""
        import time
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name=f"rsi_{self.window}",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 使用参数覆盖默认窗口
        window = params.get("window", self.window) if params else self.window

        # 计算价格变化
        delta = data["close"].diff()

        # 分离涨跌
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        # 计算 RS
        rs = gain / loss

        # 计算 RSI
        rsi = 100 - (100 / (1 + rs))

        result_data = pd.DataFrame({
            f"rsi_{window}": rsi,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name=f"rsi_{window}",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class MACDFactor(FactorCalculator):
    """MACD (Moving Average Convergence Divergence) 因子"""

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        初始化 MACD 因子。

        Args:
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="macd",
            description="MACD 指标 (DIF, DEA, MACD柱)",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["trend", "momentum", "macd"],
            data_requirements=["close"],
            parameters={
                "fast_period": self.fast_period,
                "slow_period": self.slow_period,
                "signal_period": self.signal_period,
            },
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 MACD"""
        import time
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name="macd",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 使用参数覆盖默认值
        fast_period = params.get("fast_period", self.fast_period) if params else self.fast_period
        slow_period = params.get("slow_period", self.slow_period) if params else self.slow_period
        signal_period = params.get("signal_period", self.signal_period) if params else self.signal_period

        # 计算 EMA
        ema_fast = data["close"].ewm(span=fast_period, adjust=False).mean()
        ema_slow = data["close"].ewm(span=slow_period, adjust=False).mean()

        # 计算 DIF (快线 - 慢线)
        dif = ema_fast - ema_slow

        # 计算 DEA (DIF 的 EMA)
        dea = dif.ewm(span=signal_period, adjust=False).mean()

        # 计算 MACD 柱
        macd_hist = (dif - dea) * 2

        result_data = pd.DataFrame({
            "macd_dif": dif,
            "macd_dea": dea,
            "macd_hist": macd_hist,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="macd",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class BollingerBandsFactor(FactorCalculator):
    """布林带因子"""

    def __init__(self, window: int = 20, num_std: float = 2.0):
        """
        初始化布林带因子。

        Args:
            window: 移动平均窗口
            num_std: 标准差倍数
        """
        self.window = window
        self.num_std = num_std

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="bollinger_bands",
            description="布林带指标 (上轨、中轨、下轨、位置)",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["volatility", "bands", "bollinger"],
            data_requirements=["close"],
            parameters={"window": self.window, "num_std": self.num_std},
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算布林带"""
        import time
        start_time = time.time()

        if "close" not in data.columns:
            return FactorResult(
                factor_name="bollinger_bands",
                data=pd.DataFrame(),
                metadata=self.metadata,
                calculation_time=0.0,
                success=False,
                error_message="Missing 'close' column",
            )

        # 使用参数覆盖默认值
        window = params.get("window", self.window) if params else self.window
        num_std = params.get("num_std", self.num_std) if params else self.num_std

        # 计算中轨 (移动平均)
        middle_band = data["close"].rolling(window=window).mean()

        # 计算标准差
        std = data["close"].rolling(window=window).std()

        # 计算上下轨
        upper_band = middle_band + (std * num_std)
        lower_band = middle_band - (std * num_std)

        # 计算布林带位置 (当前价格在布林带中的位置)
        bollinger_position = (data["close"] - lower_band) / (upper_band - lower_band)

        result_data = pd.DataFrame({
            "bollinger_upper": upper_band,
            "bollinger_middle": middle_band,
            "bollinger_lower": lower_band,
            "bollinger_position": bollinger_position,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="bollinger_bands",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )


class KDJFactor(FactorCalculator):
    """KDJ 因子"""

    def __init__(self, k_period: int = 9, d_period: int = 3, j_period: int = 3):
        """
        初始化 KDJ 因子。

        Args:
            k_period: K 值周期
            d_period: D 值周期
            j_period: J 值周期
        """
        self.k_period = k_period
        self.d_period = d_period
        self.j_period = j_period

    @property
    def metadata(self) -> FactorMetadata:
        return FactorMetadata(
            name="kdj",
            description="KDJ 随机指标",
            category=FactorCategory.TECHNICAL,
            frequency=FactorFrequency.DAILY,
            version="1.0.0",
            tags=["oscillator", "momentum", "kdj"],
            data_requirements=["high", "low", "close"],
            parameters={
                "k_period": self.k_period,
                "d_period": self.d_period,
                "j_period": self.j_period,
            },
        )

    def calculate(self, data: pd.DataFrame, params: dict | None = None) -> FactorResult:
        """计算 KDJ"""
        import time
        start_time = time.time()

        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in data.columns:
                return FactorResult(
                    factor_name="kdj",
                    data=pd.DataFrame(),
                    metadata=self.metadata,
                    calculation_time=0.0,
                    success=False,
                    error_message=f"Missing '{col}' column",
                )

        # 使用参数覆盖默认值
        k_period = params.get("k_period", self.k_period) if params else self.k_period
        d_period = params.get("d_period", self.d_period) if params else self.d_period

        # 计算 RSV (Raw Stochastic Value)
        low_min = data["low"].rolling(window=k_period).min()
        high_max = data["high"].rolling(window=k_period).max()
        rsv = (data["close"] - low_min) / (high_max - low_min) * 100

        # 计算 K 值
        k = rsv.ewm(com=d_period - 1, adjust=False).mean()

        # 计算 D 值
        d = k.ewm(com=d_period - 1, adjust=False).mean()

        # 计算 J 值
        j = 3 * k - 2 * d

        result_data = pd.DataFrame({
            "kdj_k": k,
            "kdj_d": d,
            "kdj_j": j,
        }, index=data.index)

        calculation_time = time.time() - start_time

        return FactorResult(
            factor_name="kdj",
            data=result_data,
            metadata=self.metadata,
            calculation_time=calculation_time,
        )
