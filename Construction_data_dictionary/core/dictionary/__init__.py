"""
Core Dictionary Modules - 核心字典模块

提供层级式高炉炼铁工业数据字典系统的基础数据结构和管理。

5 层数据层级结构：
  Work Type (工种) → Data Category (数据类别) → Data Pool (数据池)
  → Dataset (数据集) → Attribute (属性模板)

Usage:
    from Construction_data_dictionary.core.dictionary import BaseDictionary
    from Construction_data_dictionary.core.dictionary import DataCategoryDictionary
"""

from .registry import Registry, compact_key, normalize_text
from .base_dictionary import BaseDictionary, WorkType
from .data_category_dictionary import DataCategoryDictionary, DataCategory
from .data_pool_dictionary import DataPoolDictionary, DataPool
from .dataset_dictionary import DatasetDictionary, DatasetItem
from .data_attribute_dictionary import DataAttributeDictionary, AttributeTemplate

__all__ = [
    # Registry utilities
    "Registry",
    "compact_key",
    "normalize_text",
    # Work Type
    "BaseDictionary",
    "WorkType",
    # Data Category
    "DataCategoryDictionary",
    "DataCategory",
    # Data Pool
    "DataPoolDictionary",
    "DataPool",
    # Dataset
    "DatasetDictionary",
    "DatasetItem",
    # Data Attribute
    "DataAttributeDictionary",
    "AttributeTemplate",
]
