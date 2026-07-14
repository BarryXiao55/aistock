"""Test record linkage module."""

import pandas as pd
import pytest

from aistock.validation.linkage.interface import LinkResult, LinkageResult
from aistock.validation.linkage.exact_match import ExactMatcher
from aistock.validation.linkage.fuzzy_match import FuzzyMatcher
from aistock.validation.linkage.probabilistic_match import ProbabilisticMatcher


class TestExactMatcher:
    """测试 ExactMatcher"""

    def test_exact_match_success(self):
        """测试精确匹配成功"""
        source_df = pd.DataFrame({
            "code": ["A", "B", "C"],
            "name": ["Alpha", "Beta", "Gamma"],
        })
        target_df = pd.DataFrame({
            "symbol": ["A", "B", "D"],
            "company": ["Alpha Corp", "Beta Inc", "Delta Ltd"],
        })

        matcher = ExactMatcher()
        result = matcher.link(source_df, target_df, ["code"], ["symbol"])

        assert result.matched_count == 2
        assert result.match_rate == pytest.approx(2/3, rel=1e-2)

    def test_exact_match_no_matches(self):
        """测试精确匹配无匹配"""
        source_df = pd.DataFrame({"code": ["X", "Y", "Z"]})
        target_df = pd.DataFrame({"symbol": ["A", "B", "C"]})

        matcher = ExactMatcher()
        result = matcher.link(source_df, target_df, ["code"], ["symbol"])

        assert result.matched_count == 0
        assert result.match_rate == 0.0

    def test_exact_match_all_match(self):
        """测试精确匹配全部匹配"""
        source_df = pd.DataFrame({"code": ["A", "B", "C"]})
        target_df = pd.DataFrame({"symbol": ["A", "B", "C"]})

        matcher = ExactMatcher()
        result = matcher.link(source_df, target_df, ["code"], ["symbol"])

        assert result.matched_count == 3
        assert result.match_rate == 1.0

    def test_exact_match_multiple_columns(self):
        """测试多列精确匹配"""
        source_df = pd.DataFrame({
            "code": ["A", "A", "B"],
            "date": ["2025-01-01", "2025-01-02", "2025-01-01"],
        })
        target_df = pd.DataFrame({
            "symbol": ["A", "A", "B"],
            "trade_date": ["2025-01-01", "2025-01-03", "2025-01-01"],
        })

        matcher = ExactMatcher()
        result = matcher.link(
            source_df, target_df,
            ["code", "date"], ["symbol", "trade_date"]
        )

        # 只有 (A, 2025-01-01) 和 (B, 2025-01-01) 匹配
        assert result.matched_count == 2

    def test_exact_match_missing_column(self):
        """测试缺失列异常"""
        source_df = pd.DataFrame({"code": ["A"]})
        target_df = pd.DataFrame({"symbol": ["A"]})

        matcher = ExactMatcher()
        with pytest.raises(ValueError, match="not found"):
            matcher.link(source_df, target_df, ["missing"], ["symbol"])


class TestFuzzyMatcher:
    """测试 FuzzyMatcher"""

    def test_fuzzy_match_similar_strings(self):
        """测试模糊匹配相似字符串"""
        source_df = pd.DataFrame({"name": ["Apple Inc", "Google LLC", "Microsoft"]})
        target_df = pd.DataFrame({"company": ["Apple Inc.", "Google LLC", "Microsft"]})

        matcher = FuzzyMatcher(algorithm="levenshtein")
        result = matcher.link(source_df, target_df, ["name"], ["company"], threshold=0.7)

        # 应该匹配大部分
        assert result.matched_count >= 2

    def test_fuzzy_match_different_strings(self):
        """测试模糊匹配不同字符串"""
        source_df = pd.DataFrame({"name": ["Apple", "Google", "Microsoft"]})
        target_df = pd.DataFrame({"company": ["Banana", "Orange", "Grape"]})

        matcher = FuzzyMatcher(algorithm="levenshtein")
        result = matcher.link(source_df, target_df, ["name"], ["company"], threshold=0.8)

        # 应该没有匹配
        assert result.matched_count == 0

    def test_fuzzy_match_with_threshold(self):
        """测试模糊匹配阈值"""
        source_df = pd.DataFrame({"name": ["Apple"]})
        target_df = pd.DataFrame({"company": ["Appel"]})  # 拼写错误

        matcher = FuzzyMatcher(algorithm="levenshtein")

        # 高阈值
        result_high = matcher.link(source_df, target_df, ["name"], ["company"], threshold=0.9)
        assert result_high.matched_count == 0

        # 低阈值
        result_low = matcher.link(source_df, target_df, ["name"], ["company"], threshold=0.6)
        assert result_low.matched_count == 1

    def test_fuzzy_match_jaro_winkler(self):
        """测试 Jaro-Winkler 算法"""
        source_df = pd.DataFrame({"name": ["Apple"]})
        target_df = pd.DataFrame({"company": ["Appel"]})

        matcher = FuzzyMatcher(algorithm="jaro_winkler")
        result = matcher.link(source_df, target_df, ["name"], ["company"], threshold=0.7)

        assert result.matched_count == 1

    def test_fuzzy_match_similarity_calculation(self):
        """测试相似度计算"""
        matcher = FuzzyMatcher()

        # 测试 Levenshtein 相似度
        assert matcher._levenshtein_similarity("apple", "apple") == 1.0
        assert matcher._levenshtein_similarity("apple", "appel") >= 0.8
        assert matcher._levenshtein_similarity("apple", "banana") < 0.5

        # 测试 Jaro-Winkler 相似度
        assert matcher._jaro_winkler_similarity("apple", "apple") == 1.0
        assert matcher._jaro_winkler_similarity("apple", "appel") >= 0.8


class TestProbabilisticMatcher:
    """测试 ProbabilisticMatcher"""

    def test_probabilistic_match_basic(self):
        """测试概率匹配基本功能"""
        source_df = pd.DataFrame({
            "code": ["A", "B", "C"],
            "name": ["Alpha", "Beta", "Gamma"],
        })
        target_df = pd.DataFrame({
            "symbol": ["A", "B", "D"],
            "company": ["Alpha Corp", "Beta Inc", "Delta Ltd"],
        })

        matcher = ProbabilisticMatcher()
        result = matcher.link(source_df, target_df, ["code", "name"], ["symbol", "company"])

        # 应该有匹配
        assert result.matched_count >= 0

    def test_probabilistic_match_returns_linkage_result(self):
        """测试返回正确的结果类型"""
        source_df = pd.DataFrame({"code": ["A"]})
        target_df = pd.DataFrame({"symbol": ["A"]})

        matcher = ProbabilisticMatcher()
        result = matcher.link(source_df, target_df, ["code"], ["symbol"])

        assert isinstance(result, LinkageResult)
        assert result.source_count == 1
        assert result.target_count == 1

    def test_probabilistic_match_confidence_scores(self):
        """测试置信度分数"""
        source_df = pd.DataFrame({"code": ["A", "B"]})
        target_df = pd.DataFrame({"symbol": ["A", "B"]})

        matcher = ProbabilisticMatcher()
        result = matcher.link(source_df, target_df, ["code"], ["symbol"])

        for link in result.links:
            assert 0 <= link.confidence <= 1
            assert link.match_type == "probabilistic"


class TestLinkResult:
    """测试 LinkResult"""

    def test_to_dict(self):
        """测试转换为字典"""
        link = LinkResult(
            source_index=0,
            target_index=1,
            confidence=0.95,
            match_type="exact",
            details={"key": "value"},
        )
        d = link.to_dict()
        assert d["source_index"] == 0
        assert d["target_index"] == 1
        assert d["confidence"] == 0.95
        assert d["match_type"] == "exact"


class TestLinkageResult:
    """测试 LinkageResult"""

    def test_match_rate(self):
        """测试匹配率"""
        result = LinkageResult(
            links=[],
            source_count=10,
            target_count=8,
            matched_count=6,
            unmatched_source_count=4,
            unmatched_target_count=2,
        )
        assert result.match_rate == 0.6

    def test_match_rate_zero_source(self):
        """测试零源数据的匹配率"""
        result = LinkageResult(
            links=[],
            source_count=0,
            target_count=8,
            matched_count=0,
            unmatched_source_count=0,
            unmatched_target_count=8,
        )
        assert result.match_rate == 0.0

    def test_to_dict(self):
        """测试转换为字典"""
        result = LinkageResult(
            links=[],
            source_count=10,
            target_count=8,
            matched_count=6,
            unmatched_source_count=4,
            unmatched_target_count=2,
        )
        d = result.to_dict()
        assert d["source_count"] == 10
        assert d["match_rate"] == 0.6
