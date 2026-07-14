"""Factor registry for managing factor calculators."""

from typing import Any

from aistock.factors.interface import FactorCalculator, FactorMetadata, FactorCategory


class FactorRegistry:
    """因子注册表"""

    def __init__(self):
        """初始化因子注册表"""
        self._factors: dict[str, FactorCalculator] = {}
        self._metadata: dict[str, FactorMetadata] = {}

    def register(self, name: str, calculator: FactorCalculator) -> None:
        """
        注册因子。

        Args:
            name: 因子名称
            calculator: 因子计算器实例
        """
        if name in self._factors:
            raise ValueError(f"Factor '{name}' already registered")

        self._factors[name] = calculator
        self._metadata[name] = calculator.metadata

    def unregister(self, name: str) -> None:
        """
        注销因子。

        Args:
            name: 因子名称
        """
        if name not in self._factors:
            raise KeyError(f"Factor '{name}' not found")

        del self._factors[name]
        del self._metadata[name]

    def get(self, name: str) -> FactorCalculator:
        """
        获取因子计算器。

        Args:
            name: 因子名称

        Returns:
            FactorCalculator: 因子计算器实例
        """
        if name not in self._factors:
            raise KeyError(f"Factor '{name}' not found")

        return self._factors[name]

    def get_metadata(self, name: str) -> FactorMetadata:
        """
        获取因子元数据。

        Args:
            name: 因子名称

        Returns:
            FactorMetadata: 因子元数据
        """
        if name not in self._metadata:
            raise KeyError(f"Factor '{name}' not found")

        return self._metadata[name]

    def list_factors(self, category: FactorCategory | None = None) -> list[str]:
        """
        列出所有因子。

        Args:
            category: 按类别过滤（可选）

        Returns:
            list[str]: 因子名称列表
        """
        if category is None:
            return list(self._factors.keys())

        return [
            name
            for name, meta in self._metadata.items()
            if meta.category == category
        ]

    def list_metadata(self, category: FactorCategory | None = None) -> list[FactorMetadata]:
        """
        列出所有因子元数据。

        Args:
            category: 按类别过滤（可选）

        Returns:
            list[FactorMetadata]: 因子元数据列表
        """
        if category is None:
            return list(self._metadata.values())

        return [
            meta
            for meta in self._metadata.values()
            if meta.category == category
        ]

    def get_by_tag(self, tag: str) -> list[str]:
        """
        按标签获取因子。

        Args:
            tag: 标签名称

        Returns:
            list[str]: 因子名称列表
        """
        return [
            name
            for name, meta in self._metadata.items()
            if tag in meta.tags
        ]

    def __len__(self) -> int:
        """获取注册的因子数量"""
        return len(self._factors)

    def __contains__(self, name: str) -> bool:
        """检查因子是否已注册"""
        return name in self._factors

    def __repr__(self) -> str:
        return f"<FactorRegistry(factors={len(self._factors)})>"


# 全局因子注册表实例
_global_registry: FactorRegistry | None = None


def get_global_registry() -> FactorRegistry:
    """获取全局因子注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = FactorRegistry()
    return _global_registry


def register_factor(name: str, calculator: FactorCalculator) -> None:
    """注册因子到全局注册表"""
    registry = get_global_registry()
    registry.register(name, calculator)
