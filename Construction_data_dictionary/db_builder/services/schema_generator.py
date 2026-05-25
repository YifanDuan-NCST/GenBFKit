# -*- coding: utf-8 -*-
"""Schema 生成服务 - 生成前端展示和文档用的 Schema"""

from typing import Any, Dict, List, Optional

from ..models.dynamic_tables import DynamicTableRegistry
from ..schemas.database import ColumnInfo, TableInfo


class SchemaGenerator:
    """
    Schema 生成器 - 生成各种展示用的 Schema 信息

    功能:
    1. 生成数据池类型的列 Schema 定义
    2. 生成数据集的表结构信息
    3. 生成前端展示用的树形结构
    """

    # 数据池类型中文映射
    POOL_TYPE_NAMES = {
        "Binary status data": "二元状态数据",
        "Continuous time-series data": "连续时序数据",
        "Discrete time-series data": "离散时序数据",
        "Batch time-series data": "批次时序数据",
        "Controllable data": "可控数据",
        "Constraint data": "约束数据",
        "Response data": "响应数据",
        "Text data": "文本数据",
        "Image data": "图像数据",
    }

    # 数据池类型图标映射
    POOL_TYPE_ICONS = {
        "Binary status data": "🔘",
        "Continuous time-series data": "📈",
        "Discrete time-series data": "📊",
        "Batch time-series data": "📦",
        "Controllable data": "🎛️",
        "Constraint data": "⚖️",
        "Response data": "🔄",
        "Text data": "📝",
        "Image data": "🖼️",
    }

    @classmethod
    def get_pool_type_name(cls, pool_type: str) -> str:
        """获取数据池类型的中文名称"""
        return cls.POOL_TYPE_NAMES.get(pool_type, pool_type)

    @classmethod
    def get_pool_type_icon(cls, pool_type: str) -> str:
        """获取数据池类型的图标"""
        return cls.POOL_TYPE_ICONS.get(pool_type, "📁")

    @classmethod
    def generate_pool_schema(
        cls,
        pool_type: str,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        生成数据池类型的 Schema

        Args:
            pool_type: 数据池类型
            attributes: 属性字典 {attribute_id: attribute_name}，来自 meta_attribute_templates

        Returns:
            Schema 字典
        """
        schema_columns = []
        if attributes:
            for attr_id, attr_name in attributes.items():
                sa_type, nullable, _ = DynamicTableRegistry.infer_column_type(attr_name, attr_id)
                schema_columns.append({
                    "name": attr_name,
                    "type": str(sa_type),
                    "nullable": nullable,
                    "required": not nullable,
                })

        return {
            "pool_type": pool_type,
            "pool_type_zh": cls.get_pool_type_name(pool_type),
            "icon": cls.get_pool_type_icon(pool_type),
            "columns": schema_columns,
            "column_count": len(schema_columns),
        }

    @classmethod
    def generate_all_pool_schemas(
        cls,
        pool_attrs_map: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        生成所有数据池类型的 Schema

        Args:
            pool_attrs_map: 各数据池类型的属性字典 {pool_type: {attribute_id: attribute_name}}
        """
        if pool_attrs_map is None:
            pool_attrs_map = {}
        return [
            cls.generate_pool_schema(pool_type, pool_attrs_map.get(pool_type))
            for pool_type in cls.POOL_TYPE_NAMES.keys()
        ]

    @classmethod
    def generate_dataset_tree(cls, datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成数据集的树形结构

        Args:
            datasets: 数据集列表

        Returns:
            树形结构的数据
        """
        # 按工种分组
        work_types: Dict[str, Dict] = {}

        for ds in datasets:
            wt_en = ds.get("work_type_en", "")
            wt_zh = ds.get("work_type_zh", "")
            cat_en = ds.get("category_en", "")
            cat_zh = ds.get("category_zh", "")
            pool_en = ds.get("pool_en", "")
            pool_zh = ds.get("pool_zh", "")
            ds_en = ds.get("dataset_en", "")
            ds_zh = ds.get("dataset_zh", "")
            table_name = ds.get("table_name", "")

            # 工种节点
            if wt_en not in work_types:
                work_types[wt_en] = {
                    "key": f"wt_{wt_en}",
                    "work_type_en": wt_en,
                    "work_type_zh": wt_zh,
                    "categories": {},
                }

            # 类别节点
            wt_node = work_types[wt_en]
            if cat_en not in wt_node["categories"]:
                wt_node["categories"][cat_en] = {
                    "key": f"cat_{cat_en}",
                    "category_en": cat_en,
                    "category_zh": cat_zh,
                    "pools": {},
                }

            # 数据池节点
            cat_node = wt_node["categories"][cat_en]
            if pool_en not in cat_node["pools"]:
                cat_node["pools"][pool_en] = {
                    "key": f"pool_{pool_en}",
                    "pool_type": pool_en,
                    "pool_type_zh": cls.get_pool_type_name(pool_en),
                    "icon": cls.get_pool_type_icon(pool_en),
                    "datasets": [],
                }

            # 数据集节点
            pool_node = cat_node["pools"][pool_en]
            pool_node["datasets"].append({
                "key": f"ds_{ds_en}",
                "dataset_en": ds_en,
                "dataset_zh": ds_zh,
                "table_name": ds.get("table_name", ""),
                "physical_table_name": ds.get("physical_table_name", ""),
            })

        # 转换为列表格式
        result = []
        for wt_en, wt_data in work_types.items():
            wt_data["categories"] = list(wt_data["categories"].values())
            for cat in wt_data["categories"]:
                cat["pools"] = list(cat["pools"].values())
            result.append(wt_data)

        return result

    @classmethod
    def generate_statistics_schema(cls, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成统计信息的展示 Schema

        Args:
            stats: 原始统计信息

        Returns:
            展示用的统计 Schema
        """
        return {
            "overview": {
                "title": "数据概览",
                "items": [
                    {
                        "label": "工种数量",
                        "value": stats.get("total_work_types", 0),
                        "icon": "👷",
                    },
                    {
                        "label": "数据类别",
                        "value": stats.get("total_categories", 0),
                        "icon": "📁",
                    },
                    {
                        "label": "数据池",
                        "value": stats.get("total_pools", 0),
                        "icon": "🗃️",
                    },
                    {
                        "label": "数据集",
                        "value": stats.get("total_datasets", 0),
                        "icon": "📋",
                    },
                ],
            },
            "database": {
                "title": "数据库统计",
                "items": [
                    {
                        "label": "物理表数",
                        "value": stats.get("total_tables", 0),
                        "icon": "🗄️",
                    },
                    {
                        "label": "总记录数",
                        "value": stats.get("total_records", 0),
                        "icon": "📈",
                    },
                    {
                        "label": "数据库大小",
                        "value": f"{stats.get('database_size_mb', 0):.2f} MB",
                        "icon": "💾",
                    },
                ],
            },
        }
