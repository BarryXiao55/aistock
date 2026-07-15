"""Factor caching for performance optimization."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable

import pandas as pd


class FactorCache:
    """因子计算缓存"""

    def __init__(self, cache_dir: str | Path = "cache/factors", ttl: int = 3600):
        """
        初始化因子缓存。

        Args:
            cache_dir: 缓存目录
            ttl: 缓存过期时间（秒）
        """
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._ttl = ttl
        self._memory_cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """
        获取缓存值。

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值，如果不存在或过期则返回 None
        """
        # 先检查内存缓存
        if key in self._memory_cache:
            timestamp, value = self._memory_cache[key]
            if time.time() - timestamp < self._ttl:
                return value
            else:
                del self._memory_cache[key]

        # 再检查磁盘缓存
        cache_file = self._cache_dir / f"{self._hash_key(key)}.parquet"
        if cache_file.exists():
            # 检查文件修改时间
            file_time = cache_file.stat().st_mtime
            if time.time() - file_time < self._ttl:
                try:
                    value = pd.read_parquet(cache_file)
                    # 更新内存缓存
                    self._memory_cache[key] = (time.time(), value)
                    return value
                except Exception:
                    pass

        return None

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存值。

        Args:
            key: 缓存键
            value: 缓存值
        """
        # 更新内存缓存
        self._memory_cache[key] = (time.time(), value)

        # 更新磁盘缓存
        if isinstance(value, pd.DataFrame):
            cache_file = self._cache_dir / f"{self._hash_key(key)}.parquet"
            try:
                value.to_parquet(cache_file, engine="pyarrow")
            except Exception:
                pass

    def delete(self, key: str) -> None:
        """
        删除缓存。

        Args:
            key: 缓存键
        """
        # 删除内存缓存
        if key in self._memory_cache:
            del self._memory_cache[key]

        # 删除磁盘缓存
        cache_file = self._cache_dir / f"{self._hash_key(key)}.parquet"
        if cache_file.exists():
            cache_file.unlink()

    def clear(self) -> None:
        """清空所有缓存"""
        # 清空内存缓存
        self._memory_cache.clear()

        # 清空磁盘缓存
        for cache_file in self._cache_dir.glob("*.parquet"):
            cache_file.unlink()

    def _hash_key(self, key: str) -> str:
        """生成缓存键的哈希值"""
        return hashlib.sha256(key.encode()).hexdigest()

    def cache_decorator(self, ttl: int | None = None):
        """
        缓存装饰器。

        Args:
            ttl: 缓存过期时间（秒）

        Returns:
            Callable: 装饰后的函数
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # 生成缓存键
                key = f"{func.__name__}:{args}:{kwargs}"
                if ttl:
                    key = f"{key}:{ttl}"

                # 尝试获取缓存
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value

                # 执行函数
                result = func(*args, **kwargs)

                # 缓存结果
                self.set(key, result)

                return result
            return wrapper
        return decorator

    def __len__(self) -> int:
        """获取缓存条目数量"""
        return len(self._memory_cache) + len(list(self._cache_dir.glob("*.parquet")))

    def __repr__(self) -> str:
        return f"<FactorCache(ttl={self._ttl}, entries={len(self)})>"
