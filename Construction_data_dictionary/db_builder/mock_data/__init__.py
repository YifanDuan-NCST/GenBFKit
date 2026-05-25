# -*- coding: utf-8 -*-
"""
GenBFKit Mock Data Generator
============================

为 GenBFKit 框架中的所有物理数据表生成真实的虚拟数据。
支持 9 种数据池类型的所有列类型（数值、时序、布尔、文本、JSONB 等）。

使用方法:
    python -m db_builder.mock_data.main

或直接运行:
    python db_builder/mock_data/main.py

API 方式:
    POST /api/mock/generate-all  # 生成所有表数据
    POST /api/mock/generate?table_name=xxx  # 生成单个表数据
    GET  /api/mock/status  # 查看生成状态
"""

from .generator import MockDataGenerator

__all__ = ["MockDataGenerator"]
