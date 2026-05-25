# -*- coding: utf-8 -*-
"""API 路由"""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from ..services.database_manager import get_manager
from ..services.schema_generator import SchemaGenerator
from ..schemas.database import TableBuildRequest, TableBuildResponse
from ..models import AttributeTemplateModel


router = APIRouter()


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check():
    """数据库健康检查"""
    manager = get_manager()
    health = manager.health_check()
    return health.dict()


# ==================== 初始化 ====================

@router.post("/init")
async def initialize_database(json_path: Optional[str] = None):
    """
    初始化数据库

    Args:
        json_path: JSON数据文件路径

    Returns:
        初始化结果
    """
    manager = get_manager()
    result = manager.initialize_database(json_path)
    return result


@router.post("/build")
async def build_tables(
    request: TableBuildRequest = TableBuildRequest(),
):
    """
    全量构建数据库表

    Args:
        request: 建表请求参数

    Returns:
        构建结果
    """
    manager = get_manager()
    result = manager.build_tables(
        json_path=request.json_path,
        overwrite=request.overwrite,
    )
    return result.dict()


# ==================== 统计信息 ====================

@router.get("/stats")
async def get_statistics():
    """获取数据库统计信息"""
    manager = get_manager()
    stats = manager.get_statistics()
    return stats.dict()


@router.get("/stats/schema")
async def get_statistics_schema():
    """获取统计信息的展示 Schema"""
    manager = get_manager()
    stats = manager.get_statistics()
    schema = SchemaGenerator.generate_statistics_schema(stats.dict())
    return schema


# ==================== 数据集树 ====================

@router.get("/tree")
async def get_dataset_tree():
    """获取数据集树形结构"""
    manager = get_manager()
    tree = manager.get_dataset_tree()
    return tree


# ==================== 表管理 ====================

@router.get("/tables")
async def list_tables(
    pool_type: Optional[str] = Query(None, description="数据池类型过滤"),
    work_type: Optional[str] = Query(None, description="工种过滤"),
):
    """
    列出所有物理数据表

    Args:
        pool_type: 数据池类型过滤
        work_type: 工种过滤

    Returns:
        表列表
    """
    manager = get_manager()
    tables = manager.list_tables(pool_type=pool_type, work_type=work_type)
    return {"tables": tables, "total": len(tables)}


@router.get("/tables/{table_name}")
async def get_table_detail(table_name: str):
    """
    获取表详细信息

    Args:
        table_name: 表名

    Returns:
        表详情
    """
    manager = get_manager()
    schema = manager.get_table_schema(table_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    return schema


@router.get("/tables/{table_name}/sql")
async def get_table_sql(table_name: str):
    """
    获取表的建表 SQL

    Args:
        table_name: 表名

    Returns:
        SQL 语句
    """
    manager = get_manager()
    schema = manager.get_table_schema(table_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    return {"sql": schema["schema_sql"]}


# ==================== 数据池 Schema ====================

def _load_pool_attrs_map(manager) -> dict:
    """从数据库加载所有数据池的属性模板"""
    session = manager.table_builder.get_session()
    try:
        templates = session.query(AttributeTemplateModel).all()
        return {t.pool_type: t.attributes for t in templates}
    finally:
        session.close()


@router.get("/schemas/pool-types")
async def list_pool_types():
    """列出所有数据池类型"""
    manager = get_manager()
    pool_attrs_map = _load_pool_attrs_map(manager)
    pool_schemas = SchemaGenerator.generate_all_pool_schemas(pool_attrs_map)
    return {"pool_types": pool_schemas}


@router.get("/schemas/pool-types/{pool_type}")
async def get_pool_type_schema(pool_type: str):
    """
    获取指定数据池类型的 Schema

    Args:
        pool_type: 数据池类型

    Returns:
        Schema 信息
    """
    manager = get_manager()
    session = manager.table_builder.get_session()
    try:
        template = session.query(AttributeTemplateModel).filter_by(pool_type=pool_type).first()
        attrs = template.attributes if template else {}
    finally:
        session.close()
    schema = SchemaGenerator.generate_pool_schema(pool_type, attrs)
    if not schema["columns"]:
        raise HTTPException(status_code=404, detail=f"Pool type '{pool_type}' not found")
    return schema


# ==================== 导出功能 ====================

@router.post("/export/sql")
async def export_sql_script(output_path: str = "exports/schema.sql"):
    """
    导出建表 SQL 脚本

    Args:
        output_path: 输出文件路径

    Returns:
        导出结果
    """
    manager = get_manager()
    try:
        sql = manager.export_sql_script(output_path)
        return {
            "success": True,
            "message": f"SQL script exported to {output_path}",
            "path": output_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild-pool")
async def rebuild_pool_tables(pool_types: List[str] = Body(..., description="需要重建的池类型列表")):
    """
    重建指定数据池类型的所有物理表（属性模板变更后使用）

    当某个池类型的属性模板发生变更时（如新增/修改属性列），
    需要调用此接口重建该池类型下的所有物理表，以反映最新列结构。

    Args:
        pool_types: 需要重建的池类型列表，如 ["Continuous_time-series_data", "Binary_status_data"]

    Returns:
        重建结果统计
    """
    manager = get_manager()
    if not pool_types:
        raise HTTPException(status_code=400, detail="pool_types cannot be empty")
    result = manager.rebuild_pool_tables(pool_types=pool_types, overwrite=True)
    return result.dict()


@router.post("/backfill")
async def backfill_chinese_columns():
    """
    回填 meta_datasets 中缺失的中文列

    从 meta_work_types / meta_data_categories / meta_data_pools 表查中文值，
    填充到 meta_datasets 的 work_type_zh / category_zh / pool_zh 为空的记录。

    Returns:
        各字段的回填统计 {"work_type_zh": N, "category_zh": N, "pool_zh": N}
    """
    manager = get_manager()
    stats = manager.backfill_chinese_columns()
    return {"success": True, "stats": stats}


@router.post("/full-build")
async def full_build(json_path: Optional[str] = None):
    """
    一体化构建：初始化数据库 + 增量导入 + 自适应建表

    完整流程（自动依次执行，无需手动分步）：
    1. 初始化元数据表（如不存在）
    2. 元数据增量导入（幂等去重 + 属性模板 Upsert）
    3. 新增数据集的物理表构建
    4. 属性变更池类型的物理表重建

    Args:
        json_path: JSON 数据文件路径（可选，默认使用 prebuilt_full.json）

    Returns:
        完整构建结果
    """
    manager = get_manager()
    result = manager.incremental_import(json_path)
    return result


# ==================== 连接信息 ====================

@router.get("/connection")
async def get_connection_info():
    """获取数据库连接信息"""
    manager = get_manager()
    return manager.get_connection_info()
