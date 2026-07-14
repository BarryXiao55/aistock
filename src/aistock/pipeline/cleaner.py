"""Cleaner orchestrator."""

import pandas as pd

from aistock.cleaning.interface import CleaningStep
from aistock.exceptions import CleanError


class Cleaner:
    """清洗编排器 --- 按注册顺序串联执行"""

    def __init__(self, steps: list[CleaningStep]):
        self._steps = steps

    def clean(self, df: pd.DataFrame, ctx) -> tuple[pd.DataFrame, list[str]]:
        """依次执行所有步骤，返回 (清洗后DataFrame, 问题列表)"""
        issues = []
        for step in self._steps:
            try:
                df = step.clean(df, ctx)
                step_issues = step.validate(df)
                issues.extend(f"[{step.name}] {i}" for i in step_issues)
            except CleanError:
                ctx.log.error(f"cleaning step [{step.name}] failed")
                raise
        return df, issues


# Populated in Task 15 when concrete steps are implemented
from aistock.cleaning.universal import UniversalCleaner
from aistock.cleaning.adjustment import AdjustmentCleaner
from aistock.cleaning.status import StatusCleaner
from aistock.cleaning.validator import OHLCValidator

# B 级清洗步骤（基线）
STEPS_BASELINE: list[CleaningStep] = [
    UniversalCleaner(),      # 1. 去重 + 空值 + 代码格式统一
    AdjustmentCleaner(),     # 2. 复权处理（依赖步骤1的代码格式统一）
    StatusCleaner(),         # 3. 停牌/退市/ST 标记
    OHLCValidator(),         # 4. 基础 OHLC 校验
]

# C 级清洗步骤（高级）- 目前与 B 级相同，后期扩展
STEPS_ADVANCED: list[CleaningStep] = STEPS_BASELINE.copy()
