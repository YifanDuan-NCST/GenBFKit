# -*- coding: utf-8 -*-
"""元数据模型 - 存储数据集字典的元信息"""

from sqlalchemy import Column, String, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base, UUIDMixin, TimestampMixin


class WorkTypeModel(Base, UUIDMixin, TimestampMixin):
    """工种元数据表"""

    __tablename__ = "meta_work_types"

    no = Column(Integer, nullable=True, comment="序号")
    work_type_en = Column(String(200), nullable=False, comment="工种英文名")
    work_type_zh = Column(String(200), nullable=True, comment="工种中文名")

    __table_args__ = (
        Index("idx_work_type_en", "work_type_en", unique=True),
    )


class DataCategoryModel(Base, UUIDMixin, TimestampMixin):
    """数据类别元数据表"""

    __tablename__ = "meta_data_categories"

    work_type_en = Column(String(200), nullable=False, comment="工种英文名")
    work_type_zh = Column(String(200), nullable=True, comment="工种中文名")
    category_en = Column(String(500), nullable=False, comment="类别英文名")
    category_zh = Column(String(500), nullable=True, comment="类别中文名")

    __table_args__ = (
        Index("idx_category_lookup", "work_type_en", "category_en", unique=True),
    )


class DataPoolModel(Base, UUIDMixin, TimestampMixin):
    """数据池元数据表"""

    __tablename__ = "meta_data_pools"

    work_type_en = Column(String(200), nullable=True, comment="工种英文名")
    work_type_zh = Column(String(200), nullable=True, comment="工种中文名")
    category_en = Column(String(500), nullable=True, comment="类别英文名")
    category_zh = Column(String(500), nullable=True, comment="类别中文名")
    pool_en = Column(String(200), nullable=False, comment="数据池英文名")
    pool_zh = Column(String(200), nullable=True, comment="数据池中文名")

    __table_args__ = (
        Index("idx_pool_lookup", "work_type_en", "category_en", "pool_en"),
    )


class DatasetModel(Base, UUIDMixin, TimestampMixin):
    """数据集元数据表"""

    __tablename__ = "meta_datasets"

    work_type_en = Column(String(200), nullable=False, comment="工种英文名")
    work_type_zh = Column(String(200), nullable=True, comment="工种中文名")
    category_en = Column(String(500), nullable=False, comment="类别英文名")
    category_zh = Column(String(500), nullable=True, comment="类别中文名")
    pool_en = Column(String(200), nullable=False, comment="数据池英文名")
    pool_zh = Column(String(200), nullable=True, comment="数据池中文名")
    dataset_en = Column(String(500), nullable=False, comment="数据集英文名")
    dataset_zh = Column(String(500), nullable=True, comment="数据集中文名")
    dataset_zh_short = Column(String(200), nullable=True, comment="数据集中文简称")
    physical_table_name = Column(String(63), nullable=True, comment="物理表简称（截断后用于建表）")
    table_name = Column(String(200), nullable=True, comment="对应的物理表名")
    table_created = Column(String(10), default="pending", comment="表创建状态: pending/created/failed")
    record_count = Column(Integer, default=0, comment="数据记录数")

    __table_args__ = (
        Index("idx_dataset_lookup", "work_type_en", "category_en", "pool_en", "dataset_en", unique=True),
        Index("idx_dataset_table_name", "table_name"),
        Index("idx_dataset_physical_table_name", "physical_table_name"),
        Index("idx_dataset_pool_type", "pool_en"),
    )


class AttributeTemplateModel(Base, UUIDMixin, TimestampMixin):
    """属性模板元数据表"""

    __tablename__ = "meta_attribute_templates"

    pool_type = Column(String(200), nullable=False, comment="数据池类型")
    attributes = Column(JSONB, nullable=False, comment="属性字典 {attribute_id: attribute_name}")

    __table_args__ = (
        Index("idx_attr_template_pool_type", "pool_type", unique=True),
    )
