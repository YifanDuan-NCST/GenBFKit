"""Data Architecture Extension Module - 底层数据架构拓展模块。

支持外部高炉场景数据快速映射与字典结构扩展：
- Schema 验证与管理
- 字典层级 CRUD 操作
- 外部数据到字典结构的自动映射
"""

from .schema_manager import SchemaManager, SchemaValidationResult
from .crud_operations import DictionaryCRUD
from .mapper import DataMapper, MappingRule

__all__ = [
    "SchemaManager",
    "SchemaValidationResult",
    "DictionaryCRUD",
    "DataMapper",
    "MappingRule",
]