"""
Construction_data_dictionary - 高炉炼铁工业数据字典系统

提供层级式高炉炼铁工业数据字典，以统一结构组织工业数据。

5 层数据层级结构：
  Work Type (工种) → Data Category (数据类别) → Data Pool (数据池)
  → Dataset (数据集) → Attribute (属性模板)

Usage:
    from Construction_data_dictionary import DictionaryManager

    # 创建管理器实例
    mgr = DictionaryManager()

    # 加载预构建数据
    mgr.load_prebuilt_default()

    # 获取所有工种
    work_types = mgr.get_work_types()
"""

# 核心字典模块（从 core.dictionary 导入）
from .core.dictionary import (
    BaseDictionary,
    WorkType,
    DataAttributeDictionary,
    AttributeTemplate,
    DataCategoryDictionary,
    DataCategory,
    DataPoolDictionary,
    DataPool,
    DatasetDictionary,
    DatasetItem,
    Registry,
    compact_key,
    normalize_text,
)

# 核心管理器模块（从 core 导入）
from .core import (
    DictionaryManager,
    GenBFKitDictManager,
    prebuilt_default,
)

__all__ = [
    # 核心字典
    "BaseDictionary",
    "WorkType",
    "DataAttributeDictionary",
    "AttributeTemplate",
    "DataCategoryDictionary",
    "DataCategory",
    "DataPoolDictionary",
    "DataPool",
    "DatasetDictionary",
    "DatasetItem",
    "Registry",
    "compact_key",
    "normalize_text",
    # 核心管理器
    "DictionaryManager",
    "GenBFKitDictManager",
    "prebuilt_default",
]
