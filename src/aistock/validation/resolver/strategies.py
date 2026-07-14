"""Priority-based conflict resolution."""

from datetime import datetime

import pandas as pd

from aistock.validation.resolver.interface import (
    ConflictResolver, Conflict, Resolution, ResolutionResult,
)


class PriorityResolver(ConflictResolver):
    """基于优先级的冲突解决器"""

    name = "priority"
    description = "按数据源优先级解决冲突"

    def __init__(self, source_priority: dict[str, int] | None = None):
        """
        初始化优先级解决器。

        Args:
            source_priority: 数据源优先级字典，值越小优先级越高
                             例如: {"akstock": 1, "baostock": 2, "tushare": 3}
        """
        self.source_priority = source_priority or {}

    def resolve(
        self,
        conflicts: list[Conflict],
        context: dict | None = None,
    ) -> ResolutionResult:
        """执行优先级冲突解决"""
        resolutions = []

        for conflict in conflicts:
            # 从上下文获取数据源信息
            source_name = conflict.details.get("source_name", "")
            target_name = conflict.details.get("target_name", "")

            # 获取优先级
            source_priority = self.source_priority.get(source_name, 999)
            target_priority = self.source_priority.get(target_name, 999)

            # 选择优先级更高的值（值越小优先级越高）
            if source_priority <= target_priority:
                resolved_value = conflict.source_value
                resolution_method = f"priority ({source_name})"
                confidence = 0.9
            else:
                resolved_value = conflict.target_value
                resolution_method = f"priority ({target_name})"
                confidence = 0.9

            resolutions.append(Resolution(
                conflict=conflict,
                resolved_value=resolved_value,
                resolution_method=resolution_method,
                confidence=confidence,
                details={
                    "source_name": source_name,
                    "target_name": target_name,
                    "source_priority": source_priority,
                    "target_priority": target_priority,
                },
            ))

        return ResolutionResult(
            resolutions=resolutions,
            total_conflicts=len(conflicts),
            resolved_count=len(resolutions),
            unresolved_count=0,
        )


class TimestampResolver(ConflictResolver):
    """基于时间戳的冲突解决器"""

    name = "timestamp"
    description = "选择最新更新的值"

    def resolve(
        self,
        conflicts: list[Conflict],
        context: dict | None = None,
    ) -> ResolutionResult:
        """执行时间戳冲突解决"""
        resolutions = []

        for conflict in conflicts:
            # 获取时间戳
            source_ts = conflict.source_timestamp
            target_ts = conflict.target_timestamp

            # 如果没有时间戳，使用默认值
            if source_ts is None and target_ts is None:
                resolved_value = conflict.source_value
                resolution_method = "timestamp (default to source)"
                confidence = 0.5
            elif source_ts is None:
                resolved_value = conflict.target_value
                resolution_method = "timestamp (target has timestamp)"
                confidence = 0.8
            elif target_ts is None:
                resolved_value = conflict.source_value
                resolution_method = "timestamp (source has timestamp)"
                confidence = 0.8
            elif source_ts >= target_ts:
                resolved_value = conflict.source_value
                resolution_method = "timestamp (source is newer)"
                confidence = 0.95
            else:
                resolved_value = conflict.target_value
                resolution_method = "timestamp (target is newer)"
                confidence = 0.95

            resolutions.append(Resolution(
                conflict=conflict,
                resolved_value=resolved_value,
                resolution_method=resolution_method,
                confidence=confidence,
                details={
                    "source_timestamp": source_ts.isoformat() if source_ts else None,
                    "target_timestamp": target_ts.isoformat() if target_ts else None,
                },
            ))

        return ResolutionResult(
            resolutions=resolutions,
            total_conflicts=len(conflicts),
            resolved_count=len(resolutions),
            unresolved_count=0,
        )


class VotingResolver(ConflictResolver):
    """基于投票的冲突解决器"""

    name = "voting"
    description = "多数投票决定值"

    def __init__(self, sources: list[str] | None = None):
        """
        初始化投票解决器。

        Args:
            sources: 数据源名称列表
        """
        self.sources = sources or []

    def resolve(
        self,
        conflicts: list[Conflict],
        context: dict | None = None,
    ) -> ResolutionResult:
        """执行投票冲突解决"""
        resolutions = []

        for conflict in conflicts:
            # 收集所有值
            values = []
            if conflict.source_value is not None:
                values.append(conflict.source_value)
            if conflict.target_value is not None:
                values.append(conflict.target_value)

            # 如果有上下文中的其他值，也加入
            if context and "additional_values" in context:
                values.extend(context["additional_values"])

            if not values:
                resolved_value = None
                resolution_method = "voting (no values)"
                confidence = 0.0
            else:
                # 多数投票
                from collections import Counter
                value_counts = Counter(values)
                most_common = value_counts.most_common(1)[0]
                resolved_value = most_common[0]
                vote_count = most_common[1]
                total_votes = len(values)

                resolution_method = f"voting ({vote_count}/{total_votes})"
                confidence = vote_count / total_votes if total_votes > 0 else 0.0

            resolutions.append(Resolution(
                conflict=conflict,
                resolved_value=resolved_value,
                resolution_method=resolution_method,
                confidence=confidence,
                details={
                    "vote_counts": dict(Counter(values)) if values else {},
                },
            ))

        return ResolutionResult(
            resolutions=resolutions,
            total_conflicts=len(conflicts),
            resolved_count=len(resolutions),
            unresolved_count=0,
        )


class MergeResolver(ConflictResolver):
    """基于合并的冲突解决器"""

    name = "merge"
    description = "按规则合并多个值"

    def __init__(self, merge_rules: dict[str, callable] | None = None):
        """
        初始化合并解决器。

        Args:
            merge_rules: 合并规则字典，键为列名，值为合并函数
                        例如: {"name": lambda values: " / ".join(set(values))}
        """
        self.merge_rules = merge_rules or {}

    def resolve(
        self,
        conflicts: list[Conflict],
        context: dict | None = None,
    ) -> ResolutionResult:
        """执行合并冲突解决"""
        resolutions = []

        for conflict in conflicts:
            # 收集所有值
            values = []
            if conflict.source_value is not None:
                values.append(conflict.source_value)
            if conflict.target_value is not None:
                values.append(conflict.target_value)

            # 应用合并规则
            if conflict.column in self.merge_rules:
                try:
                    resolved_value = self.merge_rules[conflict.column](values)
                    resolution_method = f"merge (custom rule for {conflict.column})"
                    confidence = 0.85
                except Exception as e:
                    resolved_value = conflict.source_value
                    resolution_method = f"merge (fallback due to error: {e})"
                    confidence = 0.5
            elif not values:
                resolved_value = None
                resolution_method = "merge (no values)"
                confidence = 0.0
            elif len(values) == 1:
                resolved_value = values[0]
                resolution_method = "merge (single value)"
                confidence = 1.0
            else:
                # 默认合并：保留所有唯一值
                unique_values = list(dict.fromkeys(values))  # 保持顺序
                if all(isinstance(v, str) for v in unique_values):
                    resolved_value = " | ".join(unique_values)
                else:
                    resolved_value = unique_values[0]  # 非字符串类型取第一个
                resolution_method = "merge (default)"
                confidence = 0.7

            resolutions.append(Resolution(
                conflict=conflict,
                resolved_value=resolved_value,
                resolution_method=resolution_method,
                confidence=confidence,
                details={
                    "original_values": values,
                },
            ))

        return ResolutionResult(
            resolutions=resolutions,
            total_conflicts=len(conflicts),
            resolved_count=len(resolutions),
            unresolved_count=0,
        )
