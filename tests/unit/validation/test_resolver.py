"""Test conflict resolution module."""

from datetime import datetime, timedelta

import pytest

from aistock.validation.resolver.interface import (
    ConflictResolver, Conflict, Resolution, ResolutionResult,
)
from aistock.validation.resolver.strategies import (
    PriorityResolver, TimestampResolver, VotingResolver, MergeResolver,
)


class TestPriorityResolver:
    """测试 PriorityResolver"""

    def test_higher_priority_wins(self):
        """测试高优先级胜出"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
                details={"source_name": "akstock", "target_name": "baostock"},
            )
        ]

        resolver = PriorityResolver(source_priority={"akstock": 1, "baostock": 2})
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolution_rate == 1.0
        assert result.resolutions[0].resolved_value == 10.0  # akstock 优先级更高

    def test_lower_priority_wins(self):
        """测试低优先级胜出"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
                details={"source_name": "tushare", "target_name": "akstock"},
            )
        ]

        resolver = PriorityResolver(source_priority={"akstock": 1, "tushare": 3})
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolutions[0].resolved_value == 12.0  # akstock 优先级更高

    def test_unknown_source_default_priority(self):
        """测试未知数据源默认优先级"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
                details={"source_name": "unknown_source", "target_name": "akstock"},
            )
        ]

        resolver = PriorityResolver(source_priority={"akstock": 1})
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        # unknown_source 默认优先级 999，akstock 优先级 1，所以 akstock 胜出
        assert result.resolutions[0].resolved_value == 12.0


class TestTimestampResolver:
    """测试 TimestampResolver"""

    def test_newer_timestamp_wins(self):
        """测试较新时间戳胜出"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
                source_timestamp=yesterday,
                target_timestamp=now,
            )
        ]

        resolver = TimestampResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolutions[0].resolved_value == 12.0  # target 更新

    def test_no_timestamp_fallback(self):
        """测试无时间戳回退"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
                source_timestamp=None,
                target_timestamp=None,
            )
        ]

        resolver = TimestampResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        # 默认回退到 source
        assert result.resolutions[0].resolved_value == 10.0
        assert result.resolutions[0].confidence == 0.5

    def test_one_timestamp_wins(self):
        """测试一个有时间戳胜出"""
        now = datetime.now()

        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
                source_timestamp=None,
                target_timestamp=now,
            )
        ]

        resolver = TimestampResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolutions[0].resolved_value == 12.0  # 有时间戳的胜出


class TestVotingResolver:
    """测试 VotingResolver"""

    def test_majority_wins(self):
        """测试多数投票胜出"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=10.0,
            )
        ]

        resolver = VotingResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolutions[0].resolved_value == 10.0
        assert result.resolutions[0].confidence == 1.0

    def test_tie_breaks_to_first(self):
        """测试平局取第一个"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
            )
        ]

        resolver = VotingResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        # 平局时取第一个值
        assert result.resolutions[0].resolved_value in [10.0, 12.0]

    def test_with_additional_values(self):
        """测试带额外值的投票"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
            )
        ]

        resolver = VotingResolver()
        context = {"additional_values": [10.0, 10.0, 12.0]}
        result = resolver.resolve(conflicts, context)

        assert result.resolved_count == 1
        # 10.0 出现 3 次，12.0 出现 2 次
        assert result.resolutions[0].resolved_value == 10.0

    def test_empty_values(self):
        """测试空值"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=None,
                target_value=None,
            )
        ]

        resolver = VotingResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolutions[0].resolved_value is None
        assert result.resolutions[0].confidence == 0.0


class TestMergeResolver:
    """测试 MergeResolver"""

    def test_string_merge(self):
        """测试字符串合并"""
        conflicts = [
            Conflict(
                column="name",
                source_index=0,
                target_index=0,
                source_value="Apple",
                target_value="Apple Inc",
            )
        ]

        resolver = MergeResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert "Apple" in result.resolutions[0].resolved_value
        assert "Apple Inc" in result.resolutions[0].resolved_value

    def test_single_value(self):
        """测试单个值"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=None,
            )
        ]

        resolver = MergeResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolutions[0].resolved_value == 10.0
        assert result.resolutions[0].confidence == 1.0

    def test_custom_merge_rule(self):
        """测试自定义合并规则"""
        def average_merge(values):
            return sum(values) / len(values)

        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=10.0,
                target_value=12.0,
            )
        ]

        resolver = MergeResolver(merge_rules={"close": average_merge})
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolutions[0].resolved_value == 11.0

    def test_empty_values(self):
        """测试空值"""
        conflicts = [
            Conflict(
                column="close",
                source_index=0,
                target_index=0,
                source_value=None,
                target_value=None,
            )
        ]

        resolver = MergeResolver()
        result = resolver.resolve(conflicts)

        assert result.resolved_count == 1
        assert result.resolutions[0].resolved_value is None
        assert result.resolutions[0].confidence == 0.0


class TestConflict:
    """测试 Conflict"""

    def test_to_dict(self):
        """测试转换为字典"""
        conflict = Conflict(
            column="close",
            source_index=0,
            target_index=1,
            source_value=10.0,
            target_value=12.0,
            source_timestamp=datetime(2025, 1, 1),
            target_timestamp=datetime(2025, 1, 2),
            details={"key": "value"},
        )
        d = conflict.to_dict()
        assert d["column"] == "close"
        assert d["source_value"] == "10.0"
        assert d["target_value"] == "12.0"


class TestResolution:
    """测试 Resolution"""

    def test_to_dict(self):
        """测试转换为字典"""
        conflict = Conflict(
            column="close",
            source_index=0,
            target_index=0,
            source_value=10.0,
            target_value=12.0,
        )
        resolution = Resolution(
            conflict=conflict,
            resolved_value=10.0,
            resolution_method="priority",
            confidence=0.9,
            details={"key": "value"},
        )
        d = resolution.to_dict()
        assert d["resolved_value"] == "10.0"
        assert d["resolution_method"] == "priority"
        assert d["confidence"] == 0.9


class TestResolutionResult:
    """测试 ResolutionResult"""

    def test_resolution_rate(self):
        """测试解决率"""
        result = ResolutionResult(
            resolutions=[],
            total_conflicts=10,
            resolved_count=8,
            unresolved_count=2,
        )
        assert result.resolution_rate == 0.8

    def test_resolution_rate_zero_conflicts(self):
        """测试零冲突的解决率"""
        result = ResolutionResult(
            resolutions=[],
            total_conflicts=0,
            resolved_count=0,
            unresolved_count=0,
        )
        assert result.resolution_rate == 1.0

    def test_to_dict(self):
        """测试转换为字典"""
        result = ResolutionResult(
            resolutions=[],
            total_conflicts=10,
            resolved_count=8,
            unresolved_count=2,
        )
        d = result.to_dict()
        assert d["total_conflicts"] == 10
        assert d["resolution_rate"] == 0.8
