"""Probabilistic matching record linker."""

import pandas as pd
import numpy as np

from aistock.validation.linkage.interface import RecordLinker, LinkResult, LinkageResult


class ProbabilisticMatcher(RecordLinker):
    """概率匹配记录链接器（Fellegi-Sunter 模型）"""

    name = "probabilistic_match"
    description = "基于 Fellegi-Sunter 模型的概率匹配"

    def __init__(self, max_iterations: int = 100, tolerance: float = 1e-6):
        """
        初始化概率匹配器。

        Args:
            max_iterations: 最大迭代次数
            tolerance: 收敛阈值
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def link(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        source_columns: list[str],
        target_columns: list[str],
        threshold: float = 0.8,
    ) -> LinkageResult:
        """执行概率匹配"""
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

        # 计算比较向量
        comparison_vectors = self._compute_comparison_vectors(
            source_df, target_df, source_columns, target_columns
        )

        # 估计参数（简化版本）
        weights = self._estimate_weights(comparison_vectors)

        # 计算匹配分数
        for i, source_idx in enumerate(source_df["_source_index"]):
            best_match = None
            best_score = 0.0

            for j, target_idx in enumerate(target_df["_target_index"]):
                # 计算对数似然比
                score = self._compute_score(comparison_vectors[i][j], weights)

                if score >= threshold and score > best_score:
                    best_match = target_idx
                    best_score = score

            if best_match is not None:
                links.append(LinkResult(
                    source_index=int(source_idx),
                    target_index=int(best_match),
                    confidence=best_score,
                    match_type="probabilistic",
                    details={"method": "fellegi_sunter"},
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

    def _compute_comparison_vectors(
        self,
        source_df: pd.DataFrame,
        target_df: pd.DataFrame,
        source_columns: list[str],
        target_columns: list[str],
    ) -> list[list[dict]]:
        """计算比较向量"""
        comparison_vectors = []

        for _, source_row in source_df.iterrows():
            row_vectors = []
            for _, target_row in target_df.iterrows():
                vector = {}
                for src_col, tgt_col in zip(source_columns, target_columns):
                    src_val = source_row[src_col]
                    tgt_val = target_row[tgt_col]

                    # 计算比较结果
                    if pd.isna(src_val) or pd.isna(tgt_val):
                        vector[f"{src_col}_agree"] = 0  # 缺失值视为不匹配
                        vector[f"{src_col}_disagree"] = 0
                        vector[f"{src_col}_missing"] = 1
                    elif str(src_val).lower() == str(tgt_val).lower():
                        vector[f"{src_col}_agree"] = 1
                        vector[f"{src_col}_disagree"] = 0
                        vector[f"{src_col}_missing"] = 0
                    else:
                        vector[f"{src_col}_agree"] = 0
                        vector[f"{src_col}_disagree"] = 1
                        vector[f"{src_col}_missing"] = 0

                row_vectors.append(vector)
            comparison_vectors.append(row_vectors)

        return comparison_vectors

    def _estimate_weights(self, comparison_vectors: list[list[dict]]) -> dict:
        """估计匹配权重（简化版本）"""
        if not comparison_vectors or not comparison_vectors[0]:
            return {}

        # 获取所有特征名
        features = list(comparison_vectors[0][0].keys())

        # 简化的权重估计：使用一致率作为权重
        weights = {}
        for feature in features:
            agrees = sum(
                cv[feature]
                for row_vectors in comparison_vectors
                for cv in row_vectors
                if feature in cv
            )
            total = len(comparison_vectors) * len(comparison_vectors[0])

            if total > 0:
                agree_rate = agrees / total
                # 权重 = log(agree_rate / (1 - agree_rate + 1e-10))
                weights[feature] = np.log(agree_rate / (1 - agree_rate + 1e-10) + 1e-10)

        return weights

    def _compute_score(self, comparison_vector: dict, weights: dict) -> float:
        """计算匹配分数"""
        score = 0.0
        for feature, value in comparison_vector.items():
            if feature in weights:
                score += weights[feature] * value

        # 转换为概率 (sigmoid)
        probability = 1 / (1 + np.exp(-score))

        return probability
