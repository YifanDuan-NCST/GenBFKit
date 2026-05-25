# -*- coding: utf-8 -*-
"""
GenBFKit 数据库构建模块

提供从 JSON 数据全量构建 PostgreSQL 数据库表的功能。

主要功能:
1. 元数据管理 - 存储数据集字典的层级结构
2. 动态表构建 - 根据9种数据池类型为每个Dataset创建物理表
3. Web API - FastAPI 接口提供数据管理功能
4. 可视化界面 - HTML Dashboard 展示数据库状态

使用示例:
    from db_builder.services.database_manager import DatabaseManager
    from db_builder.config import DatabaseSettings

    # 配置数据库
    db_settings = DatabaseSettings(
        host="localhost",
        port=5432,
        database="genbfkit",
        username="postgres",
        password="your_password",
    )

    # 初始化管理器
    manager = DatabaseManager(db_settings=db_settings, json_path="prebuilt_full.json")

    # 初始化数据库
    manager.initialize_database()

    # 构建所有表
    result = manager.build_tables()

    # 获取统计
    stats = manager.get_statistics()
"""

from .config import DatabaseSettings, AppSettings, Settings, settings
from .models import (
    Base,
    UUIDMixin,
    TimestampMixin,
    WorkTypeModel,
    DataCategoryModel,
    DataPoolModel,
    DatasetModel,
    AttributeTemplateModel,
    DynamicTableRegistry,
    create_dynamic_table_model,
)
from .services.database_manager import DatabaseManager, get_manager

__version__ = "1.0.0"

__all__ = [
    # 配置
    "DatabaseSettings",
    "AppSettings",
    "Settings",
    "settings",
    # 模型
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "WorkTypeModel",
    "DataCategoryModel",
    "DataPoolModel",
    "DatasetModel",
    "AttributeTemplateModel",
    "DynamicTableRegistry",
    "create_dynamic_table_model",
    # 服务
    "DatabaseManager",
    "get_manager",
    # 版本
    "__version__",
]
