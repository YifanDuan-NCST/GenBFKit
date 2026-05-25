# -*- coding: utf-8 -*-
"""数据库相关的 Pydantic Schemas"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WorkTypeSchema(BaseModel):
    """工种 Schema"""

    work_type_en: str = Field(..., description="工种英文名")
    work_type_zh: Optional[str] = Field(None, description="工种中文名")
    no: Optional[int] = Field(None, description="序号")


class DataCategorySchema(BaseModel):
    """数据类别 Schema"""

    work_type_en: str = Field(..., description="工种英文名")
    work_type_zh: Optional[str] = Field(None, description="工种中文名")
    category_en: str = Field(..., description="类别英文名")
    category_zh: Optional[str] = Field(None, description="类别中文名")


class DataPoolSchema(BaseModel):
    """数据池 Schema"""

    work_type_en: Optional[str] = Field(None, description="工种英文名")
    work_type_zh: Optional[str] = Field(None, description="工种中文名")
    category_en: Optional[str] = Field(None, description="类别英文名")
    category_zh: Optional[str] = Field(None, description="类别中文名")
    pool_en: str = Field(..., description="数据池英文名")
    pool_zh: Optional[str] = Field(None, description="数据池中文名")


class DatasetSchema(BaseModel):
    """数据集 Schema"""

    work_type_en: str = Field(..., description="工种英文名")
    work_type_zh: Optional[str] = Field(None, description="工种中文名")
    category_en: str = Field(..., description="类别英文名")
    category_zh: Optional[str] = Field(None, description="类别中文名")
    pool_en: str = Field(..., description="数据池英文名")
    pool_zh: Optional[str] = Field(None, description="数据池中文名")
    dataset_en: str = Field(..., description="数据集英文名")
    dataset_zh: Optional[str] = Field(None, description="数据集中文名")
    dataset_zh_short: Optional[str] = Field(None, description="数据集中文简称")


class AttributeTemplateSchema(BaseModel):
    """属性模板 Schema"""

    pool_type: str = Field(..., description="数据池类型")
    attributes: dict[str, str] = Field(..., description="属性字典 {attribute_id: attribute_name}")


class TableBuildRequest(BaseModel):
    """建表请求"""

    json_path: Optional[str] = Field(None, description="JSON 数据文件路径（可选，默认使用初始化时指定的路径）")
    overwrite: bool = Field(False, description="是否覆盖已存在的表")
    batch_size: int = Field(100, description="每批处理的表数量")
    create_indexes: bool = Field(True, description="是否创建索引")


class ColumnInfo(BaseModel):
    """列信息"""

    name: str
    type: str
    nullable: bool
    default: Optional[str] = None
    comment: Optional[str] = None


class TableInfo(BaseModel):
    """表信息"""

    table_name: str = Field(..., description="表名")
    schema_name: str = Field(default="public", description="Schema 名")
    columns: list[ColumnInfo] = Field(..., description="列信息列表")
    row_count: Optional[int] = Field(None, description="行数")
    data_pool: Optional[str] = Field(None, description="所属数据池")
    dataset_zh: Optional[str] = Field(None, description="数据集中文名")
    work_type: Optional[str] = Field(None, description="所属工种")


class PoolTypeStats(BaseModel):
    """数据池类型统计"""

    pool_type: str
    pool_type_zh: Optional[str] = None
    total_tables: int = 0
    total_records: int = 0


class WorkTypeStats(BaseModel):
    """工种统计"""

    work_type_en: str
    work_type_zh: Optional[str] = None
    no: Optional[int] = None
    categories: int = 0
    pools: int = 0
    datasets: int = 0


class DatabaseStats(BaseModel):
    """数据库统计"""

    total_work_types: int = 0
    total_categories: int = 0
    total_pools: int = 0
    total_datasets: int = 0
    total_attribute_templates: int = 0
    total_tables: int = 0
    total_records: int = 0
    database_size_mb: Optional[float] = None
    pool_types_stats: list[PoolTypeStats] = []
    work_types_stats: list[WorkTypeStats] = []


class TableBuildResponse(BaseModel):
    """建表响应"""

    success: bool
    message: str
    tables_created: int = 0
    tables_skipped: int = 0
    tables_failed: int = 0
    errors: list[str] = []
    duration_seconds: float = 0.0


class BuildProgress(BaseModel):
    """构建进度"""

    total: int
    completed: int
    failed: int
    current_table: Optional[str] = None
    percentage: float = 0.0


class HealthCheckResponse(BaseModel):
    """健康检查响应"""

    status: str
    database_connected: bool
    metadata_tables_exist: bool
    json_file_valid: bool
    message: Optional[str] = None
