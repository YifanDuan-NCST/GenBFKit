"""
字典 CRUD 操作

对数据字典的 5 层层级提供完整的增、删、改、查操作。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from ..core.data_dictionary import (
    DataDictionary,
    WorkType,
    DataCategory,
    DataPool,
    Dataset,
    DataAttribute,
)
from .schema_manager import SchemaManager, SchemaValidationResult

logger = logging.getLogger(__name__)


class DictionaryCRUD:
    """
    数据字典 CRUD 操作。

    对 GenBFKit 的 5 层数据字典层级提供标准化增删改查接口。

    Usage:
        crud = DictionaryCRUD(data_dict)
        crud.add_work_type("New process", "新工艺")
        crud.add_category("New process", "System - Equipment - Function")
        crud.add_dataset("New process", "System - Equipment - Function",
                         "Continuous time-series data", "new_param")
    """

    def __init__(self, data_dict: DataDictionary):
        self._dict = data_dict
        self._schema = SchemaManager()

    # ────── Work Type ──────

    def add_work_type(self, name_en: str, name_zh: str = "", no: int = 0) -> Tuple[bool, str]:
        """添加新工种。"""
        # 验证
        validation = self._schema.validate_work_type(name_en, name_zh)
        if not validation.is_valid:
            return False, "; ".join(validation.errors)

        if name_en in self._dict.work_types:
            return False, f"Work type '{name_en}' already exists"

        wt = WorkType(name_en=name_en, name_zh=name_zh, no=no or (len(self._dict.work_types) + 1))
        self._dict.add_work_type(wt)
        logger.info(f"[CRUD] Added work type: {name_en}")
        return True, f"Work type '{name_en}' added successfully"

    def update_work_type(self, name_en: str, name_zh: Optional[str] = None) -> bool:
        """更新工种信息。"""
        if name_en not in self._dict.work_types:
            return False
        wt = self._dict.work_types[name_en]
        if name_zh is not None:
            wt.name_zh = name_zh
        return True

    def delete_work_type(self, name_en: str) -> Tuple[bool, str]:
        """删除工种及其关联数据。"""
        if name_en not in self._dict.work_types:
            return False, f"Work type '{name_en}' not found"

        # 获取关联的数据集数量
        related_datasets = [ds for ds in self._dict.datasets if ds.work_type_en == name_en]
        if related_datasets:
            logger.warning(
                f"[CRUD] Deleting work type '{name_en}' will also remove "
                f"{len(related_datasets)} related datasets"
            )

        self._dict.remove_work_type(name_en)
        return True, f"Work type '{name_en}' and {len(related_datasets)} related datasets deleted"

    # ────── Category ──────

    def add_category(
        self, work_type_en: str, category_en: str, category_zh: str = ""
    ) -> Tuple[bool, str]:
        """添加新数据类别。"""
        if work_type_en not in self._dict.work_types:
            return False, f"Work type '{work_type_en}' not found"

        validation = self._schema.validate_category(category_en, work_type_en)
        if not validation.is_valid:
            return False, "; ".join(validation.errors)

        existing = self._dict.categories.get(work_type_en, [])
        if any(c.category_en == category_en for c in existing):
            return False, f"Category '{category_en}' already exists under '{work_type_en}'"

        cat = DataCategory(
            work_type_en=work_type_en,
            category_en=category_en,
            category_zh=category_zh,
        )
        if work_type_en not in self._dict.categories:
            self._dict.categories[work_type_en] = []
        self._dict.categories[work_type_en].append(cat)

        logger.info(f"[CRUD] Added category '{category_en}' under '{work_type_en}'")
        return True, f"Category added successfully"

    def delete_category(self, work_type_en: str, category_en: str) -> Tuple[bool, str]:
        """删除数据类别。"""
        if work_type_en not in self._dict.categories:
            return False, f"No categories found for work type '{work_type_en}'"

        before = len(self._dict.categories[work_type_en])
        self._dict.categories[work_type_en] = [
            c for c in self._dict.categories[work_type_en] if c.category_en != category_en
        ]
        removed = before - len(self._dict.categories[work_type_en])

        if removed == 0:
            return False, f"Category '{category_en}' not found"

        # 同时删除关联数据集
        self._dict.datasets = [
            ds for ds in self._dict.datasets
            if not (ds.work_type_en == work_type_en and ds.category_en == category_en)
        ]

        return True, f"Category '{category_en}' and related datasets removed"

    # ────── Dataset ──────

    def add_dataset(
        self,
        work_type_en: str,
        category_en: str,
        pool_en: str,
        dataset_en: str,
        dataset_zh: str = "",
        dataset_zh_short: str = "",
    ) -> Tuple[bool, str]:
        """添加新数据集/参数。"""
        # 验证
        validation = self._schema.validate_dataset(dataset_en, pool_en, work_type_en, category_en)
        if not validation.is_valid:
            return False, "; ".join(validation.errors)

        # 检查是否已存在
        exists = any(
            ds.dataset_en == dataset_en
            and ds.work_type_en == work_type_en
            and ds.category_en == category_en
            for ds in self._dict.datasets
        )
        if exists:
            return False, f"Dataset '{dataset_en}' already exists in this context"

        ds = Dataset(
            work_type_en=work_type_en,
            category_en=category_en,
            pool_en=pool_en,
            dataset_en=dataset_en,
            dataset_zh=dataset_zh,
            dataset_zh_short=dataset_zh_short or dataset_zh,
        )
        self._dict.add_dataset(ds)

        logger.info(f"[CRUD] Added dataset '{dataset_en}' (pool: {pool_en})")
        return True, f"Dataset '{dataset_en}' added successfully"

    def update_dataset(
        self,
        dataset_en: str,
        work_type_en: str = "",
        **kwargs,
    ) -> bool:
        """更新数据集信息。"""
        for ds in self._dict.datasets:
            if ds.dataset_en == dataset_en:
                if work_type_en and ds.work_type_en != work_type_en:
                    continue
                for k, v in kwargs.items():
                    if hasattr(ds, k):
                        setattr(ds, k, v)
                return True
        return False

    def delete_dataset(self, dataset_en: str, work_type_en: str = "") -> Tuple[bool, str]:
        """删除数据集。"""
        original = len(self._dict.datasets)
        self._dict.remove_dataset(dataset_en, work_type_en)
        if len(self._dict.datasets) < original:
            return True, f"Dataset '{dataset_en}' deleted"
        return False, f"Dataset '{dataset_en}' not found"

    # ────── Attribute ──────

    def add_attribute(
        self,
        pool_en: str,
        attribute_name: str,
        data_type: str = "float",
        description: str = "",
    ) -> Tuple[bool, str]:
        """添加新属性。"""
        validation = self._schema.validate_attribute(attribute_name, pool_en)
        if not validation.is_valid:
            return False, "; ".join(validation.errors)

        attr = DataAttribute(
            pool_en=pool_en,
            attribute_name=attribute_name,
            data_type=data_type,
            description=description,
        )
        self._dict.add_attribute(attr)
        return True, f"Attribute '{attribute_name}' added to pool '{pool_en}'"

    def list_pool_attributes(self, pool_en: str) -> List[DataAttribute]:
        """列出指定数据池的所有属性。"""
        return self._dict.get_attributes_for_pool(pool_en)

    # ────── 批量操作 ──────

    def bulk_add_datasets(
        self, datasets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量添加数据集。"""
        results = {"success": 0, "failed": 0, "errors": []}
        for ds_data in datasets:
            ok, msg = self.add_dataset(
                work_type_en=ds_data.get("work_type_en", ""),
                category_en=ds_data.get("category_en", ""),
                pool_en=ds_data.get("pool_en", ""),
                dataset_en=ds_data.get("dataset_en", ""),
                dataset_zh=ds_data.get("dataset_zh", ""),
            )
            if ok:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(msg)
        return results

    def search(self, keyword: str) -> Dict[str, Any]:
        """关键词搜索所有层级。"""
        kw = keyword.lower()
        result = {
            "work_types": [],
            "categories": [],
            "datasets": [],
            "attributes": [],
        }

        # Work types
        for wt in self._dict.work_types.values():
            if kw in wt.name_en.lower() or kw in wt.name_zh.lower():
                result["work_types"].append(wt.name_en)

        # Categories
        for cats in self._dict.categories.values():
            for cat in cats:
                if kw in cat.category_en.lower() or kw in cat.category_zh.lower():
                    result["categories"].append(cat.category_en)

        # Datasets
        for ds in self._dict.datasets:
            if kw in ds.dataset_en.lower() or kw in ds.dataset_zh.lower():
                result["datasets"].append(ds.dataset_en)

        # Attributes
        for attrs in self._dict.attributes.values():
            for attr in attrs:
                if kw in attr.attribute_name.lower():
                    result["attributes"].append(attr.attribute_name)

        return result