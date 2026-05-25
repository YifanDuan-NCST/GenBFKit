"""
Dictionary Manager - The backbone of GenBFKit's five-level chain-like architecture.

Manages the prebuilt data architecture with the hierarchy:
    work type (8) → data category (98) → data pool (9) → dataset/params (2128) → data attribute (49)

Provides CRUD operations and chain-like mapping rules for the entire data dictionary.
"""

import json
import os
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────
# Pydantic models for each hierarchy level
# ──────────────────────────────────────────────────────────
class WorkType(BaseModel):
    """Level 1: Work type (工序类型)"""
    no: int = Field(description="Sequential number")
    work_type_en: str = Field(description="English name")
    work_type_zh: str = Field(description="Chinese name")


class DataCategory(BaseModel):
    """Level 2: Data category (数据类别), naming rule: Process system - Subordinate equipment - Function"""
    work_type_en: str = Field(description="Parent work type (English)")
    category_en: str = Field(description="Category name (English)")
    category_zh: str = Field(description="Category name (Chinese)")


class DataPool(BaseModel):
    """Level 3: Data pool (数据池)"""
    pool_en: str = Field(description="Pool name (English)")
    pool_zh: str = Field(description="Pool name (Chinese)")


class Dataset(BaseModel):
    """Level 4: Dataset / Parameter (核心参数)"""
    work_type_en: str = Field(description="Parent work type (English)")
    category_en: str = Field(description="Parent category (English)")
    pool_en: str = Field(description="Parent pool (English)")
    dataset_en: str = Field(description="Parameter name (English)")
    dataset_zh: str = Field(description="Parameter name (Chinese)")
    dataset_zh_short: str = Field(default="", description="Short Chinese name")


class AttributeTemplate(BaseModel):
    """Level 5: Data attribute template (数据属性模板)"""
    pool_en: str = Field(description="Associated data pool")
    base_attributes: dict[str, str] = Field(description="Common base attributes (attribute_1 ~ attribute_6)")
    unique_attributes: dict[str, str] = Field(description="Pool-specific unique attributes")


class DictionarySnapshot(BaseModel):
    """Complete snapshot of the prebuilt data architecture."""
    work_types: list[WorkType] = Field(default_factory=list)
    categories: list[DataCategory] = Field(default_factory=list)
    pools: list[DataPool] = Field(default_factory=list)
    datasets: list[Dataset] = Field(default_factory=list)
    attribute_templates: dict[str, AttributeTemplate] = Field(default_factory=dict)


class DictionaryManager:
    """
    Dictionary Manager - Central hub for the five-level chain-like data dictionary.

    Responsibilities:
      - Load & parse the prebuilt JSON data architecture
      - Provide chain-like traversal: work_type → category → pool → dataset → attribute
      - Support CRUD operations on each hierarchy level
      - Maintain referential integrity across the five levels

    Design principles:
      - Immutable hierarchy structure (no level addition/removal)
      - Content-level mutations only (add/modify/delete entries within existing levels)
      - All mutations respect cross-level foreign key constraints
    """

    def __init__(self, json_path: Optional[str] = None):
        self._snapshot = DictionarySnapshot()
        # Index structures for O(1) lookups
        self._wt_index: dict[str, WorkType] = {}           # work_type_en -> WorkType
        self._cat_index: dict[str, list[DataCategory]] = {} # work_type_en -> [DataCategory]
        self._pool_index: dict[str, DataPool] = {}          # pool_en -> DataPool
        self._ds_by_wt: dict[str, list[Dataset]] = {}       # work_type_en -> [Dataset]
        self._ds_by_cat: dict[str, list[Dataset]] = {}      # category_en -> [Dataset]
        self._ds_by_pool: dict[str, list[Dataset]] = {}     # pool_en -> [Dataset]
        self._ds_index: dict[str, Dataset] = {}             # dataset_en -> Dataset

        if json_path:
            self.load(json_path)

    # ──────────────────────────────────────────────────────
    # Loading
    # ──────────────────────────────────────────────────────
    def load(self, json_path: str) -> None:
        """Load the prebuilt data architecture from a JSON file."""
        logger.info(f"Loading data dictionary from: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Parse work types
        self._snapshot.work_types = [WorkType(**wt) for wt in raw.get("base_work_types", [])]
        for wt in self._snapshot.work_types:
            self._wt_index[wt.work_type_en] = wt

        # Parse categories
        self._snapshot.categories = [DataCategory(**c) for c in raw.get("categories", [])]
        for cat in self._snapshot.categories:
            self._cat_index.setdefault(cat.work_type_en, []).append(cat)

        # Parse pools
        self._snapshot.pools = [DataPool(**p) for p in raw.get("pools", [])]
        for pool in self._snapshot.pools:
            self._pool_index[pool.pool_en] = pool

        # Parse datasets (params)
        self._snapshot.datasets = [Dataset(**d) for d in raw.get("datasets", [])]
        for ds in self._snapshot.datasets:
            self._ds_by_wt.setdefault(ds.work_type_en, []).append(ds)
            self._ds_by_cat.setdefault(ds.category_en, []).append(ds)
            self._ds_by_pool.setdefault(ds.pool_en, []).append(ds)
            self._ds_index[ds.dataset_en] = ds

        # Parse attribute templates
        for pool_en, attrs in raw.get("attribute_templates", {}).items():
            base_attrs = {k: v for k, v in attrs.items()
                         if int(k.split("_")[1]) <= 6}
            unique_attrs = {k: v for k, v in attrs.items()
                           if int(k.split("_")[1]) > 6}
            self._snapshot.attribute_templates[pool_en] = AttributeTemplate(
                pool_en=pool_en,
                base_attributes=base_attrs,
                unique_attributes=unique_attrs,
            )

        logger.info(
            f"Dictionary loaded: {len(self._snapshot.work_types)} work types, "
            f"{len(self._snapshot.categories)} categories, "
            f"{len(self._snapshot.pools)} pools, "
            f"{len(self._snapshot.datasets)} datasets, "
            f"{len(self._snapshot.attribute_templates)} attribute templates"
        )

    # ──────────────────────────────────────────────────────
    # Chain-like retrieval API
    # ──────────────────────────────────────────────────────
    def get_work_types(self) -> list[WorkType]:
        """Level 1: Get all work types."""
        return self._snapshot.work_types

    def get_categories_by_work_type(self, work_type_en: str) -> list[DataCategory]:
        """Level 1→2: Get categories under a specific work type."""
        return self._cat_index.get(work_type_en, [])

    def get_pools(self) -> list[DataPool]:
        """Level 3: Get all data pools."""
        return self._snapshot.pools

    def get_pool(self, pool_en: str) -> Optional[DataPool]:
        """Get a specific pool by name."""
        return self._pool_index.get(pool_en)

    def get_datasets_by_work_type(self, work_type_en: str) -> list[Dataset]:
        """Level 1→4: Get all datasets under a work type."""
        return self._ds_by_wt.get(work_type_en, [])

    def get_datasets_by_category(self, category_en: str) -> list[Dataset]:
        """Level 2→4: Get all datasets under a category."""
        return self._ds_by_cat.get(category_en, [])

    def get_datasets_by_pool(self, pool_en: str) -> list[Dataset]:
        """Level 3→4: Get all datasets in a pool."""
        return self._ds_by_pool.get(pool_en, [])

    def get_dataset(self, dataset_en: str) -> Optional[Dataset]:
        """Get a specific dataset by English name."""
        return self._ds_index.get(dataset_en)

    def get_attributes_by_pool(self, pool_en: str) -> Optional[AttributeTemplate]:
        """Level 3→5 or 4→5: Get attribute template for a pool."""
        return self._snapshot.attribute_templates.get(pool_en)

    def get_all_datasets(self) -> list[Dataset]:
        """Get all 2128 datasets."""
        return self._snapshot.datasets

    # ──────────────────────────────────────────────────────
    # Full chain traversal
    # ──────────────────────────────────────────────────────
    def chain_traverse(
        self,
        work_type_en: Optional[str] = None,
        category_en: Optional[str] = None,
        pool_en: Optional[str] = None,
    ) -> list[Dataset]:
        """
        Execute chain-like retrieval following the five-level architecture.

        Traversal path:
            work_type → category → pool → datasets → attributes

        Each level acts as a filter; None means "no filter at this level".
        Returns the filtered list of datasets (params).
        """
        results = self._snapshot.datasets

        if work_type_en:
            results = [d for d in results if d.work_type_en == work_type_en]

        if category_en:
            results = [d for d in results if d.category_en == category_en]

        if pool_en:
            results = [d for d in results if d.pool_en == pool_en]

        return results

    # ──────────────────────────────────────────────────────
    # CRUD operations (content-level only, hierarchy is immutable)
    # ──────────────────────────────────────────────────────
    def add_dataset(self, dataset: Dataset) -> bool:
        """Add a new dataset (param) entry. Validates foreign keys first."""
        if dataset.work_type_en not in self._wt_index:
            logger.error(f"Foreign key violation: work_type '{dataset.work_type_en}' not found")
            return False
        if dataset.dataset_en in self._ds_index:
            logger.error(f"Dataset '{dataset.dataset_en}' already exists")
            return False
        self._snapshot.datasets.append(dataset)
        self._ds_by_wt.setdefault(dataset.work_type_en, []).append(dataset)
        self._ds_by_cat.setdefault(dataset.category_en, []).append(dataset)
        self._ds_by_pool.setdefault(dataset.pool_en, []).append(dataset)
        self._ds_index[dataset.dataset_en] = dataset
        logger.info(f"Added dataset: {dataset.dataset_en}")
        return True

    def delete_dataset(self, dataset_en: str) -> bool:
        """Delete a dataset entry by English name."""
        ds = self._ds_index.pop(dataset_en, None)
        if ds is None:
            logger.error(f"Dataset '{dataset_en}' not found")
            return False
        self._snapshot.datasets.remove(ds)
        self._ds_by_wt.get(ds.work_type_en, []).remove(ds) if ds.work_type_en in self._ds_by_wt else None
        self._ds_by_cat.get(ds.category_en, []).remove(ds) if ds.category_en in self._ds_by_cat else None
        self._ds_by_pool.get(ds.pool_en, []).remove(ds) if ds.pool_en in self._ds_by_pool else None
        logger.info(f"Deleted dataset: {dataset_en}")
        return True

    def update_dataset(self, dataset_en: str, **kwargs) -> bool:
        """Update fields of an existing dataset."""
        ds = self._ds_index.get(dataset_en)
        if ds is None:
            logger.error(f"Dataset '{dataset_en}' not found")
            return False
        for k, v in kwargs.items():
            if hasattr(ds, k):
                setattr(ds, k, v)
        logger.info(f"Updated dataset: {dataset_en}")
        return True

    # ──────────────────────────────────────────────────────
    # Export
    # ──────────────────────────────────────────────────────
    def export_json(self) -> dict:
        """Export the full data architecture as a JSON-serializable dict."""
        return self._snapshot.model_dump()

    def get_statistics(self) -> dict:
        """Get statistics about the current dictionary state."""
        from collections import Counter
        wt_dist = Counter(d.work_type_en for d in self._snapshot.datasets)
        pool_dist = Counter(d.pool_en for d in self._snapshot.datasets)
        cat_dist = Counter(d.category_en for d in self._snapshot.datasets)
        return {
            "total_work_types": len(self._snapshot.work_types),
            "total_categories": len(self._snapshot.categories),
            "total_pools": len(self._snapshot.pools),
            "total_datasets": len(self._snapshot.datasets),
            "total_attribute_templates": len(self._snapshot.attribute_templates),
            "dataset_by_work_type": dict(wt_dist),
            "dataset_by_pool": dict(pool_dist),
            "top_categories": dict(cat_dist.most_common(10)),
        }
