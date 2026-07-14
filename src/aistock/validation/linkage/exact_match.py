"""Exact matching record linker."""

import pandas as pd

from aistock.validation.linkage.interface import RecordLinker, LinkResult, LinkageResult


class ExactMatcher(RecordLinker):
    """精确匹配记录链接器"""

    name = "exact_match"
    description = "基于精确匹配的记录链接"

    def link(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        source_columns: list[str],
        target_columns: list[str],
        threshold: float = 0.8,
    ) -> LinkageResult:
        """执行精确匹配"""
        links = []
        matched_target_indices = set()

        # 验证列是否存在
        for col in source_columns:
            if col not in source_df.columns:
                raise ValueError(f"Column '{col}' not found in source DataFrame")

        for col in target_columns:
            if col not in target_df.columns:
                raise ValueError(f"Column '{col}' not found in target DataFrame")

        # 构建源表的匹配键
        source_df = source_df.copy()
        source_df["_source_index"] = range(len(source_df))
        source_df["_source_key"] = source_df[source_columns].apply(
            lambda row: tuple(str(v) for v in row), axis=1
        )

        # 构建目标表的匹配键
        target_df = target_df.copy()
        target_df["_target_index"] = range(len(target_df))
        target_df["_target_key"] = target_df[target_columns].apply(
            lambda row: tuple(str(v) for v in row), axis=1
        )

        # 创建目标表的查找字典
        target_lookup = {}
        for _, row in target_df.iterrows():
            key = row["_target_key"]
            if key not in target_lookup:
                target_lookup[key] = []
            target_lookup[key].append(row["_target_index"])

        # 执行匹配
        for _, row in source_df.iterrows():
            source_key = row["_source_key"]
            source_index = row["_source_index"]

            if source_key in target_lookup:
                for target_index in target_lookup[source_key]:
                    links.append(LinkResult(
                        source_index=int(source_index),
                        target_index=int(target_index),
                        confidence=1.0,
                        match_type="exact",
                        details={"source_key": source_key, "target_key": source_key},
                    ))
                    matched_target_indices.add(target_index)

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
