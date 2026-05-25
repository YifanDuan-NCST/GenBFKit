"""
数据映射器

实现外部数据到 GenBFKit 数据字典的自动映射与适配。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..core.data_dictionary import (
    DataDictionary,
    Dataset,
    DataPoolType,
    STANDARD_DATA_POOLS,
)

logger = logging.getLogger(__name__)


@dataclass
class MappingRule:
    """
    映射规则。

    定义外部列名/参数名到数据字典参数的映射关系。
    """
    source_column: str                    # 外部数据列名
    target_dataset: str                   # 目标数据集/参数名
    target_work_type: str = ""            # 目标工种
    target_category: str = ""             # 目标数据类别
    target_pool: str = ""                 # 目标数据池
    unit: str = ""                        # 单位（可选）
    conversion_factor: float = 1.0        # 单位换算系数
    data_type: str = "float"              # 数据类型
    is_required: bool = True              # 是否必填

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_column": self.source_column,
            "target_dataset": self.target_dataset,
            "target_work_type": self.target_work_type,
            "target_category": self.target_category,
            "target_pool": self.target_pool,
            "unit": self.unit,
            "conversion_factor": self.conversion_factor,
            "data_type": self.data_type,
            "is_required": self.is_required,
        }


@dataclass
class MappingResult:
    """映射结果。"""
    success: bool = True
    mapped_columns: int = 0
    unmapped_columns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    mapped_data: Optional[pd.DataFrame] = None


class DataMapper:
    """
    数据映射器。

    将外部数据源的列名/参数名自动或手动映射到
    GenBFKit 数据字典的标准参数体系。

    Usage:
        mapper = DataMapper(data_dict)
        mapper.add_rule(MappingRule(...))
        result = mapper.map_dataframe(external_df)
    """

    def __init__(self, data_dictionary: Optional[DataDictionary] = None):
        self._dict = data_dictionary
        self._rules: List[MappingRule] = []
        self._auto_discovery_enabled = True

    def add_rule(self, rule: MappingRule) -> None:
        """添加映射规则。"""
        self._rules.append(rule)

    def add_rules(self, rules: List[MappingRule]) -> None:
        """批量添加映射规则。"""
        self._rules.extend(rules)

    def clear_rules(self) -> None:
        """清除所有映射规则。"""
        self._rules.clear()

    def auto_discover_rules(
        self,
        columns: List[str],
        similarity_threshold: float = 0.6,
    ) -> List[MappingRule]:
        """
        自动发现映射规则。

        基于列名与数据字典参数名的语义相似度自动生成映射。

        Args:
            columns: 外部数据列名列表
            similarity_threshold: 相似度阈值

        Returns:
            自动发现的映射规则列表
        """
        if self._dict is None:
            logger.warning("No data dictionary loaded, cannot auto-discover")
            return []

        discovered = []

        for col in columns:
            col_lower = col.lower().replace("_", " ").replace("-", " ")

            # 在数据字典的 datasets 中搜索
            best_match = None
            best_score = 0.0

            for ds in self._dict.datasets:
                ds_lower = ds.dataset_en.lower()
                # 简单字符串匹配
                if col_lower == ds_lower:
                    best_match = ds
                    best_score = 1.0
                    break

                # 包含关系
                if col_lower in ds_lower or ds_lower in col_lower:
                    score = min(len(col_lower), len(ds_lower)) / max(len(col_lower), len(ds_lower))
                    if score > best_score:
                        best_score = score
                        best_match = ds

                # 词级匹配
                col_words = set(col_lower.split())
                ds_words = set(ds_lower.split())
                if col_words and ds_words:
                    overlap = len(col_words & ds_words)
                    word_score = overlap / max(len(col_words), len(ds_words))
                    if word_score > best_score:
                        best_score = word_score
                        best_match = ds

            if best_match and best_score >= similarity_threshold:
                rule = MappingRule(
                    source_column=col,
                    target_dataset=best_match.dataset_en,
                    target_work_type=best_match.work_type_en,
                    target_category=best_match.category_en,
                    target_pool=best_match.pool_en,
                )
                discovered.append(rule)
                logger.info(f"[MAP] Auto-mapped '{col}' -> '{best_match.dataset_en}' (score={best_score:.2f})")

        return discovered

    def map_dataframe(
        self,
        df: pd.DataFrame,
        rules: Optional[List[MappingRule]] = None,
    ) -> MappingResult:
        """
        映射外部 DataFrame 到字典结构。

        Args:
            df: 外部数据 DataFrame
            rules: 映射规则（若未提供，使用已注册的规则）

        Returns:
            映射结果
        """
        active_rules = rules if rules is not None else self._rules

        # 自动发现未匹配的列
        mapped_columns = set()
        unmapped_columns = []

        for col in df.columns:
            matched = False
            for rule in active_rules:
                if rule.source_column == col:
                    mapped_columns.add(col)
                    matched = True
                    break
            if not matched:
                unmapped_columns.append(col)

        # 尝试自动发现未匹配列
        if self._auto_discovery_enabled and unmapped_columns:
            auto_rules = self.auto_discover_rules(unmapped_columns)
            if auto_rules:
                active_rules = list(active_rules) + auto_rules
                for rule in auto_rules:
                    mapped_columns.add(rule.source_column)
                unmapped_columns = [c for c in unmapped_columns if c not in mapped_columns]

        # 构建映射后的数据
        mapped_data = pd.DataFrame()
        warnings = []

        for rule in active_rules:
            if rule.source_column in df.columns:
                # 单位换算
                if rule.conversion_factor != 1.0:
                    mapped_data[rule.target_dataset] = df[rule.source_column] * rule.conversion_factor
                else:
                    mapped_data[rule.target_dataset] = df[rule.source_column]

                # 类型转换
                if rule.data_type == "float" and mapped_data[rule.target_dataset].dtype != "float64":
                    mapped_data[rule.target_dataset] = mapped_data[rule.target_dataset].astype(float)

        # 检查必填列
        for rule in active_rules:
            if rule.is_required and rule.source_column not in df.columns:
                warnings.append(
                    f"Required column '{rule.source_column}' not found in data"
                )

        return MappingResult(
            success=len(unmapped_columns) < len(df.columns),
            mapped_columns=len(mapped_columns),
            unmapped_columns=unmapped_columns,
            warnings=warnings,
            mapped_data=mapped_data if not mapped_data.empty else None,
        )

    def detect_pool_type(self, df: pd.DataFrame) -> str:
        """
        自动检测数据对应的数据池类型。

        通过 DataFrame 的列特征推断最匹配的数据池类型。
        """
        features = set(df.columns.str.lower())
        # 检查列名是否包含关键词（支持部分匹配）
        def _has_keyword(keywords):
            for f in features:
                for kw in keywords:
                    if kw in f:
                        return True
            return False

        # 特征匹配得分
        pool_scores = {}
        for pool_type in STANDARD_DATA_POOLS:
            pool_scores[pool_type.name_en] = 0.0

            # 时序数据特征
            if any(t in features for t in ["timestamp", "time", "datetime"]):
                if "continuous" in pool_type.name_en.lower():
                    pool_scores[pool_type.name_en] += 2.0
                if "discrete" in pool_type.name_en.lower():
                    pool_scores[pool_type.name_en] += 1.0

            # 图像数据特征
            if _has_keyword(["image", "picture", "photo"]):
                if "image" in pool_type.name_en.lower():
                    pool_scores[pool_type.name_en] += 3.0

            # 文本数据特征
            if _has_keyword(["text", "content", "description", "note"]):
                if "text" in pool_type.name_en.lower():
                    pool_scores[pool_type.name_en] += 3.0

            # 状态/二值数据特征
            if _has_keyword(["status", "state", "flag", "binary"]):
                if "binary" in pool_type.name_en.lower() or "status" in pool_type.name_en.lower():
                    pool_scores[pool_type.name_en] += 2.0

        if pool_scores:
            best_pool = max(pool_scores, key=pool_scores.get)
            if pool_scores[best_pool] > 0:
                return best_pool

        return "Continuous time-series data"  # 默认返回连续时序数据

    def summary(self) -> Dict[str, Any]:
        """获取映射器摘要。"""
        return {
            "rules_count": len(self._rules),
            "auto_discovery": self._auto_discovery_enabled,
            "dictionary_loaded": self._dict is not None,
        }