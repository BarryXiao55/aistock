"""Fuzzy matching record linker."""

import pandas as pd
from difflib import SequenceMatcher

from aistock.validation.linkage.interface import RecordLinker, LinkResult, LinkageResult


class FuzzyMatcher(RecordLinker):
    """模糊匹配记录链接器"""

    name = "fuzzy_match"
    description = "基于模糊匹配的记录链接"

    def __init__(self, algorithm: str = "levenshtein"):
        """
        初始化模糊匹配器。

        Args:
            algorithm: 匹配算法 "levenshtein" | "jaro_winkler" | "soundex"
        """
        self.algorithm = algorithm

    def link(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        source_columns: list[str],
        target_columns: list[str],
        threshold: float = 0.8,
    ) -> LinkageResult:
        """执行模糊匹配"""
        links = []
        matched_target_indices = set()

        # 验证列是否存在
        for col in source_columns:
            if col not in source_df.columns:
                raise ValueError(f"Column '{col}' not found in source DataFrame")

        for col in target_columns:
            if col not in target_df.columns:
                raise ValueError(f"Column '{col}' not found in target DataFrame")

        # 复制数据
        source_df = source_df.copy()
        source_df["_source_index"] = range(len(source_df))

        target_df = target_df.copy()
        target_df["_target_index"] = range(len(target_df))

        # 执行匹配
        for _, source_row in source_df.iterrows():
            source_index = source_row["_source_index"]
            best_match = None
            best_confidence = 0.0

            for _, target_row in target_df.iterrows():
                target_index = target_row["_target_index"]

                # 计算匹配分数
                confidence = self._calculate_similarity(
                    source_row, target_row, source_columns, target_columns
                )

                if confidence >= threshold and confidence > best_confidence:
                    best_match = target_index
                    best_confidence = confidence

            if best_match is not None:
                links.append(LinkResult(
                    source_index=int(source_index),
                    target_index=int(best_match),
                    confidence=best_confidence,
                    match_type="fuzzy",
                    details={"algorithm": self.algorithm},
                ))
                matched_target_indices.add(best_match)

        # 计算未匹配数量
        unmatched_source = len(source_df) - len(set(link.source_index for link in links))
        unmatched_target = len(target_df) - len(matched_target_indices)

        return LinkageResult(
            links=links,
            source_count=len(source_df),
            target_count=len(target_df),
            matched_count=len(links),
            unmatched_source_count=unmatched_source,
            unmatched_target_count=unmatched_target,
        )

    def _calculate_similarity(
        self,
        source_row: pd.Series,
        target_row: pd.Series,
        source_columns: list[str],
        target_columns: list[str],
    ) -> float:
        """计算两行之间的相似度"""
        similarities = []

        for src_col, tgt_col in zip(source_columns, target_columns):
            src_val = str(source_row[src_col]) if pd.notna(source_row[src_col]) else ""
            tgt_val = str(target_row[tgt_col]) if pd.notna(target_row[tgt_col]) else ""

            if self.algorithm == "levenshtein":
                sim = self._levenshtein_similarity(src_val, tgt_val)
            elif self.algorithm == "jaro_winkler":
                sim = self._jaro_winkler_similarity(src_val, tgt_val)
            else:
                sim = self._levenshtein_similarity(src_val, tgt_val)

            similarities.append(sim)

        # 返回平均相似度
        return sum(similarities) / len(similarities) if similarities else 0.0

    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """计算 Levenshtein 相似度"""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        matcher = SequenceMatcher(None, s1.lower(), s2.lower())
        return matcher.ratio()

    def _jaro_winkler_similarity(self, s1: str, s2: str) -> float:
        """计算 Jaro-Winkler 相似度"""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        # 简化的 Jaro-Winkler 实现
        s1_lower = s1.lower()
        s2_lower = s2.lower()

        # 计算匹配字符
        match_distance = max(len(s1_lower), len(s2_lower)) // 2 - 1
        match_distance = max(0, match_distance)

        s1_matches = [False] * len(s1_lower)
        s2_matches = [False] * len(s2_lower)

        matches = 0
        transpositions = 0

        for i in range(len(s1_lower)):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len(s2_lower))

            for j in range(start, end):
                if s2_matches[j] or s1_lower[i] != s2_lower[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

        if matches == 0:
            return 0.0

        # 计算换位
        k = 0
        for i in range(len(s1_lower)):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1_lower[i] != s2_lower[k]:
                transpositions += 1
            k += 1

        jaro = (matches / len(s1_lower) + matches / len(s2_lower) +
                (matches - transpositions / 2) / matches) / 3

        # Winkler 修改
        prefix = 0
        for i in range(min(len(s1_lower), len(s2_lower), 4)):
            if s1_lower[i] == s2_lower[i]:
                prefix += 1
            else:
                break

        return jaro + prefix * 0.1 * (1 - jaro)
