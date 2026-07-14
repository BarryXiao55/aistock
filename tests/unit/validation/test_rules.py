"""Test validation rules."""

import pandas as pd
import pytest

from aistock.validation.interface import ValidationResult
from aistock.validation.rules.uniqueness import UniqueRule, UniqueCombinationRule
from aistock.validation.rules.nullability import NotNullRule, NotNullCombinationRule
from aistock.validation.rules.range import RangeRule, AcceptedValuesRule
from aistock.validation.rules.relationship import RelationshipRule, CrossReferenceRule


class TestUniqueRule:
    """测试 UniqueRule"""

    def test_unique_values_pass(self):
        """测试唯一值通过"""
        df = pd.DataFrame({"code": ["A", "B", "C", "D"]})
        rule = UniqueRule("code")
        result = rule.validate(df)
        assert result.passed is True
        assert result.rule_name == "unique"

    def test_duplicate_values_fail(self):
        """测试重复值失败"""
        df = pd.DataFrame({"code": ["A", "B", "A", "C"]})
        rule = UniqueRule("code")
        result = rule.validate(df)
        assert result.passed is False
        assert result.details["duplicated_count"] == 1

    def test_missing_column_fail(self):
        """测试缺失列失败"""
        df = pd.DataFrame({"name": ["A", "B"]})
        rule = UniqueRule("code")
        result = rule.validate(df)
        assert result.passed is False
        assert "not found" in result.message


class TestUniqueCombinationRule:
    """测试 UniqueCombinationRule"""

    def test_unique_combination_pass(self):
        """测试唯一组合通过"""
        df = pd.DataFrame({
            "code": ["A", "A", "B", "B"],
            "date": ["2025-01-01", "2025-01-02", "2025-01-01", "2025-01-02"],
        })
        rule = UniqueCombinationRule(["code", "date"])
        result = rule.validate(df)
        assert result.passed is True

    def test_duplicate_combination_fail(self):
        """测试重复组合失败"""
        df = pd.DataFrame({
            "code": ["A", "A", "A"],
            "date": ["2025-01-01", "2025-01-01", "2025-01-02"],
        })
        rule = UniqueCombinationRule(["code", "date"])
        result = rule.validate(df)
        assert result.passed is False


class TestNotNullRule:
    """测试 NotNullRule"""

    def test_no_nulls_pass(self):
        """测试无空值通过"""
        df = pd.DataFrame({"code": ["A", "B", "C"]})
        rule = NotNullRule("code")
        result = rule.validate(df)
        assert result.passed is True

    def test_nulls_fail(self):
        """测试有空值失败"""
        df = pd.DataFrame({"code": ["A", None, "C"]})
        rule = NotNullRule("code")
        result = rule.validate(df)
        assert result.passed is False
        assert result.details["null_count"] == 1

    def test_missing_column_fail(self):
        """测试缺失列失败"""
        df = pd.DataFrame({"name": ["A", "B"]})
        rule = NotNullRule("code")
        result = rule.validate(df)
        assert result.passed is False


class TestNotNullCombinationRule:
    """测试 NotNullCombinationRule"""

    def test_no_nulls_pass(self):
        """测试无空值通过"""
        df = pd.DataFrame({
            "code": ["A", "B"],
            "date": ["2025-01-01", "2025-01-02"],
        })
        rule = NotNullCombinationRule(["code", "date"])
        result = rule.validate(df)
        assert result.passed is True

    def test_nulls_fail(self):
        """测试有空值失败"""
        df = pd.DataFrame({
            "code": ["A", None],
            "date": ["2025-01-01", "2025-01-02"],
        })
        rule = NotNullCombinationRule(["code", "date"])
        result = rule.validate(df)
        assert result.passed is False


class TestRangeRule:
    """测试 RangeRule"""

    def test_within_range_pass(self):
        """测试在范围内通过"""
        df = pd.DataFrame({"price": [10.0, 20.0, 30.0]})
        rule = RangeRule("price", min_value=5.0, max_value=35.0)
        result = rule.validate(df)
        assert result.passed is True

    def test_below_min_fail(self):
        """测试低于最小值失败"""
        df = pd.DataFrame({"price": [1.0, 20.0, 30.0]})
        rule = RangeRule("price", min_value=5.0, max_value=35.0)
        result = rule.validate(df)
        assert result.passed is False
        assert any(v["type"] == "below_min" for v in result.details["violations"])

    def test_above_max_fail(self):
        """测试超过最大值失败"""
        df = pd.DataFrame({"price": [10.0, 20.0, 40.0]})
        rule = RangeRule("price", min_value=5.0, max_value=35.0)
        result = rule.validate(df)
        assert result.passed is False
        assert any(v["type"] == "above_max" for v in result.details["violations"])


class TestAcceptedValuesRule:
    """测试 AcceptedValuesRule"""

    def test_accepted_values_pass(self):
        """测试接受的值通过"""
        df = pd.DataFrame({"status": ["active", "inactive", "active"]})
        rule = AcceptedValuesRule("status", ["active", "inactive", "pending"])
        result = rule.validate(df)
        assert result.passed is True

    def test_invalid_values_fail(self):
        """测试无效值失败"""
        df = pd.DataFrame({"status": ["active", "unknown", "active"]})
        rule = AcceptedValuesRule("status", ["active", "inactive"])
        result = rule.validate(df)
        assert result.passed is False
        assert "unknown" in result.details["invalid_values"]


class TestRelationshipRule:
    """测试 RelationshipRule"""

    def test_valid_relationship_pass(self):
        """测试有效引用通过"""
        source_df = pd.DataFrame({"customer_id": [1, 2, 3]})
        reference_df = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
        rule = RelationshipRule("customer_id", reference_df, "id")
        result = rule.validate(source_df)
        assert result.passed is True

    def test_missing_reference_fail(self):
        """测试缺失引用失败"""
        source_df = pd.DataFrame({"customer_id": [1, 2, 99]})
        reference_df = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
        rule = RelationshipRule("customer_id", reference_df, "id")
        result = rule.validate(source_df)
        assert result.passed is False
        assert 99 in result.details["missing_values"]


class TestCrossReferenceRule:
    """测试 CrossReferenceRule"""

    def test_matching_references_pass(self):
        """测试匹配的引用通过"""
        source_df = pd.DataFrame({"code": ["A", "B", "C"]})
        target_df = pd.DataFrame({"symbol": ["A", "B", "C"]})
        rule = CrossReferenceRule(source_df, "code", target_df, "symbol")
        result = rule.validate()
        assert result.passed is True

    def test_mismatch_references_fail(self):
        """测试不匹配的引用失败"""
        source_df = pd.DataFrame({"code": ["A", "B", "X"]})
        target_df = pd.DataFrame({"symbol": ["A", "B", "C"]})
        rule = CrossReferenceRule(source_df, "code", target_df, "symbol", direction="both")
        result = rule.validate()
        assert result.passed is False
        assert result.details["missing_in_target_count"] == 1
        assert result.details["missing_in_source_count"] == 1

    def test_source_to_target_only(self):
        """测试仅检查源到目标"""
        source_df = pd.DataFrame({"code": ["A", "B", "X"]})
        target_df = pd.DataFrame({"symbol": ["A", "B", "C"]})
        rule = CrossReferenceRule(source_df, "code", target_df, "symbol", direction="source_to_target")
        result = rule.validate()
        assert result.passed is False
        assert result.details["missing_in_target_count"] == 1
        assert result.details["missing_in_source_count"] == 0


class TestValidationResult:
    """测试 ValidationResult"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = ValidationResult(
            rule_name="test",
            passed=True,
            message="Test passed",
            details={"key": "value"},
        )
        d = result.to_dict()
        assert d["rule_name"] == "test"
        assert d["passed"] is True
        assert d["message"] == "Test passed"
        assert d["details"]["key"] == "value"
