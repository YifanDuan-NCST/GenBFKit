"""
Schema 管理器

管理数据字典的 Schema 验证，确保所有扩展操作符合 GenBFKit 的数据规范。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ..core.data_dictionary import (
    STANDARD_DATA_POOLS,
    DataPoolType,
)

logger = logging.getLogger(__name__)

# 预构建数据架构的层级约束
MAX_WORK_TYPES = 20
MAX_CATEGORIES_PER_WT = 50
MAX_DATASETS = 5000
MAX_NAME_LENGTH = 128


class ValidationSeverity(Enum):
    """验证严重级别。"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class SchemaValidationResult:
    """Schema 验证结果。"""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def merge(self, other: "SchemaValidationResult") -> "SchemaValidationResult":
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self

    def summary(self) -> str:
        parts = []
        if self.is_valid:
            parts.append("✓ Valid")
        else:
            parts.append(f"✗ Invalid ({len(self.errors)} errors)")
        if self.warnings:
            parts.append(f"({len(self.warnings)} warnings)")
        return " | ".join(parts)


class SchemaManager:
    """
    Schema 管理器。

    验证数据字典结构扩展是否符合 GenBFKit 规范。
    核心原则：不能修改内置的 5 层层级架构。
    """

    def __init__(self):
        self._custom_pools: Set[str] = set()

    def validate_work_type(self, name_en: str, name_zh: str = "") -> SchemaValidationResult:
        """验证新的工种。"""
        result = SchemaValidationResult()

        if not name_en or not name_en.strip():
            result.errors.append("Work type name_en cannot be empty")
            result.is_valid = False
        elif len(name_en) > MAX_NAME_LENGTH:
            result.errors.append(f"Work type name_en too long ({len(name_en)} > {MAX_NAME_LENGTH})")
            result.is_valid = False

        return result

    def validate_category(
        self,
        category_en: str,
        work_type_en: str,
    ) -> SchemaValidationResult:
        """验证新的数据类别。"""
        result = SchemaValidationResult()

        if not category_en or not category_en.strip():
            result.errors.append("Category name cannot be empty")
            result.is_valid = False
            return result

        # Data category 命名规范: "Process system - Subordinate equipment - function"
        parts = category_en.split(" - ")
        if len(parts) < 2:
            result.warnings.append(
                f"Category '{category_en}' does not follow "
                f"'System - Equipment - Function' naming convention"
            )

        return result

    def validate_pool(self, pool_en: str) -> SchemaValidationResult:
        """验证数据池类型。"""
        result = SchemaValidationResult()

        if not pool_en or not pool_en.strip():
            result.errors.append("Pool name cannot be empty")
            result.is_valid = False
            return result

        # 检查是否为内置标准池
        is_standard = any(p.name_en == pool_en for p in STANDARD_DATA_POOLS)
        if not is_standard:
            result.warnings.append(
                f"Pool '{pool_en}' is not a standard pool type. "
                f"Standard types: {[p.name_en for p in STANDARD_DATA_POOLS]}"
            )

        return result

    def validate_dataset(
        self,
        dataset_en: str,
        pool_en: str,
        work_type_en: str = "",
        category_en: str = "",
    ) -> SchemaValidationResult:
        """验证新的数据集/参数。"""
        result = SchemaValidationResult()

        if not dataset_en or not dataset_en.strip():
            result.errors.append("Dataset name cannot be empty")
            result.is_valid = False

        if len(dataset_en) > MAX_NAME_LENGTH:
            result.warnings.append(
                f"Dataset name too long ({len(dataset_en)} > {MAX_NAME_LENGTH})"
            )

        return result

    def validate_attribute(
        self,
        attribute_name: str,
        pool_en: str,
    ) -> SchemaValidationResult:
        """验证数据属性。"""
        result = SchemaValidationResult()

        if not attribute_name or not attribute_name.strip():
            result.errors.append("Attribute name cannot be empty")
            result.is_valid = False

        return result

    def validate_hierarchy_integrity(
        self,
        current_counts: Dict[str, int],
        proposed_changes: Dict[str, int],
    ) -> SchemaValidationResult:
        """
        验证层级架构完整性。

        确保扩展不破坏 "work type → data category → data pool → dataset → data attribute"
        的基本架构。
        """
        result = SchemaValidationResult()

        total_datasets = current_counts.get("datasets", 0) + proposed_changes.get("datasets", 0)
        if total_datasets > MAX_DATASETS:
            result.warnings.append(
                f"Total datasets ({total_datasets}) exceeds recommended maximum ({MAX_DATASETS})"
            )

        total_wt = current_counts.get("work_types", 0) + proposed_changes.get("work_types", 0)
        if total_wt > MAX_WORK_TYPES:
            result.errors.append(
                f"Total work types ({total_wt}) exceeds maximum ({MAX_WORK_TYPES})"
            )
            result.is_valid = False

        return result

    def validate_import_data(
        self,
        data: Dict[str, Any],
    ) -> SchemaValidationResult:
        """
        验证导入的外部数据是否符合字典架构。

        核心规则：
        1. 不能修改 5 层层级
        2. 必须包含层级归属信息
        """
        result = SchemaValidationResult()

        if "work_type_en" not in data and "category_en" not in data:
            result.errors.append(
                "Import data must specify at least work_type_en or category_en "
                "to maintain hierarchy linkage"
            )
            result.is_valid = False

        if "pool_en" in data:
            pool_result = self.validate_pool(data["pool_en"])
            result.merge(pool_result)

        return result