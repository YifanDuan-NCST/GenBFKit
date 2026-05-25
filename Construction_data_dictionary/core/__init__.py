"""
Core Module - 核心模块

提供数据字典的统一管理器和预构建数据。

包含:
    - DictionaryManager: 统一管理器，协调所有字典
    - prebuilt_default: 内置预构建数据
"""

from .dict_manager import DictionaryManager, GenBFKitDictManager
from . import prebuilt_default

__all__ = [
    "DictionaryManager",
    "GenBFKitDictManager",
    "prebuilt_default",
]
