# -*- coding: utf-8 -*-
"""数据库管理器 - 统一的数据库操作接口"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session, sessionmaker

from ..config import DatabaseSettings, Settings, settings
from ..models import Base, DatasetModel, AttributeTemplateModel
from ..schemas.database import (
    DatabaseStats,
    TableBuildResponse,
    HealthCheckResponse,
)
from .table_builder import TableBuilder
from .schema_generator import SchemaGenerator


class DatabaseManager:
    """
    数据库管理器 - 提供统一的数据库操作接口

    功能:
    1. 数据库连接管理
    2. 元数据表初始化
    3. 从JSON文件全量构建表
    4. 数据库健康检查
    5. 统计信息查询
    """

    def __init__(
        self,
        db_settings: Optional[DatabaseSettings] = None,
        json_path: Optional[str | Path] = None,
    ):
        """
        初始化数据库管理器

        Args:
            db_settings: 数据库配置
            json_path: JSON数据文件路径
        """
        self.db_settings = db_settings or settings.database
        self.json_path = Path(json_path) if json_path else None
        self.table_builder = TableBuilder(self.db_settings)

    def get_connection_info(self) -> Dict[str, Any]:
        """获取数据库连接信息（隐藏密码）"""
        return {
            "host": self.db_settings.host,
            "port": self.db_settings.port,
            "database": self.db_settings.database,
            "username": self.db_settings.username,
            "display_url": self.db_settings.display_url,
        }

    def health_check(self) -> HealthCheckResponse:
        """
        执行数据库健康检查

        Returns:
            健康检查结果
        """
        response = HealthCheckResponse(
            status="unknown",
            database_connected=False,
            metadata_tables_exist=False,
            json_file_valid=False,
        )

        # 检查数据库连接
        connected, msg = self.table_builder.check_database_connection()
        response.database_connected = connected
        response.message = msg

        if not connected:
            response.status = "error"
            return response

        # 检查元数据表是否存在
        inspector = inspect(self.table_builder.engine)
        meta_tables = ["meta_work_types", "meta_data_categories", "meta_data_pools",
                      "meta_datasets", "meta_attribute_templates"]
        response.metadata_tables_exist = all(t in inspector.get_table_names() for t in meta_tables)

        # 检查JSON文件
        if self.json_path:
            response.json_file_valid = self.json_path.exists()

        # 确定状态
        if response.metadata_tables_exist and response.json_file_valid:
            response.status = "healthy"
        elif response.metadata_tables_exist:
            response.status = "partial"
        else:
            response.status = "initializing"

        return response

    def initialize_database(self, json_path: Optional[str | Path] = None) -> Dict[str, Any]:
        """
        初始化数据库

        Args:
            json_path: JSON数据文件路径

        Returns:
            初始化结果
        """
        if json_path:
            self.json_path = Path(json_path)

        result = {
            "success": True,
            "message": "",
            "steps": [],
        }

        # 1. 创建元数据表
        init_ok = self.table_builder.init_metadata_tables()
        result["steps"].append({
            "step": "Create metadata tables",
            "success": init_ok,
            "message": "Metadata tables created" if init_ok else "Failed to create metadata tables",
        })

        if not init_ok:
            result["success"] = False
            result["message"] = "Failed to initialize database"
            return result

        # 2. 导入JSON数据
        if self.json_path and self.json_path.exists():
            try:
                data = self.table_builder.load_json_data(self.json_path)
                session = self.table_builder.get_session()
                try:
                    stats = self.table_builder.import_metadata_from_json(data, session=session)
                    result["steps"].append({
                        "step": "Import metadata from JSON",
                        "success": True,
                        "message": f"Imported: datasets={stats.get('datasets', 0)}, "
                                   f"attribute_templates={stats.get('attribute_templates', 0)} "
                                   f"(new={stats.get('attribute_templates_new', 0)}, "
                                   f"updated={stats.get('attribute_templates_updated', 0)})",
                        "data": stats,
                    })

                    # 3. 自动回填缺失的中文列
                    backfill_stats = self.table_builder.backfill_missing_chinese(session=session)
                    result["steps"].append({
                        "step": "Backfill Chinese columns",
                        "success": True,
                        "message": f"work_type_zh={backfill_stats['work_type_zh']}, "
                                   f"category_zh={backfill_stats['category_zh']}, "
                                   f"pool_zh={backfill_stats['pool_zh']}",
                    })
                except Exception as e:
                    result["steps"].append({
                        "step": "Import metadata from JSON",
                        "success": False,
                        "message": f"Error: {str(e)[:100]}",
                    })
            except Exception as e:
                result["steps"].append({
                    "step": "Load JSON data",
                    "success": False,
                    "message": f"Error: {str(e)[:100]}",
                })

        result["message"] = "Database initialized successfully"
        return result

    def build_tables(
        self,
        json_path: Optional[str | Path] = None,
        overwrite: bool = False,
    ) -> TableBuildResponse:
        """
        构建所有物理数据表（默认增量模式）

        增量模式：只处理 table_created='pending' 的新增数据集，
        已创建的表默认跳过，除非指定 overwrite=True。

        Args:
            json_path: JSON数据文件路径
            overwrite: 是否覆盖已存在的表

        Returns:
            构建结果
        """
        if json_path:
            self.json_path = Path(json_path)

        if not self.json_path:
            return TableBuildResponse(
                success=False,
                message="JSON file path not provided",
            )

        return self.table_builder.build_all_physical_tables(
            json_path=self.json_path,
            overwrite=overwrite,
        )

    def rebuild_pool_tables(
        self,
        pool_types: List[str],
        overwrite: bool = True,
    ) -> TableBuildResponse:
        """
        重建指定数据池类型的所有物理表（用于属性模板变更后）

        当某个池类型的属性模板发生变更时（如新增属性或修改属性名），
        需要重建该池类型下的所有物理表以反映最新的列结构。

        Args:
            pool_types: 需要重建的池类型列表
            overwrite: 必须为 True（删除旧表重建新表）

        Returns:
            重建结果
        """
        return self.table_builder.rebuild_pool_physical_tables(
            pool_types=pool_types,
            overwrite=overwrite,
        )

    def incremental_import(
        self,
        json_path: Optional[str | Path] = None,
    ) -> Dict[str, Any]:
        """
        增量导入 JSON 数据（一体化入口，完整流程）

        自动完成：
        1. 元数据增量导入（幂等去重 + 属性模板 Upsert）
        2. 新增数据集的物理表构建（table_created='pending' 的）
        3. 属性变更池类型的物理表重建

        Args:
            json_path: JSON数据文件路径

        Returns:
            完整结果，含 import_stats、build_response、rebuild_pool_types
        """
        if json_path:
            self.json_path = Path(json_path)

        result: Dict[str, Any] = {
            "success": True,
            "message": "",
            "import_stats": {},
            "build_response": {},
            "rebuild_pool_types": [],
        }

        if not self.json_path or not self.json_path.exists():
            result["success"] = False
            result["message"] = f"JSON file not found: {self.json_path}"
            return result

        # Step 1: 元数据导入（Upsert，含属性变更检测）
        data = self.table_builder.load_json_data(self.json_path)
        session = self.table_builder.get_session()
        try:
            import_stats = self.table_builder.import_metadata_from_json(data, session=session)
            result["import_stats"] = import_stats
            result["rebuild_pool_types"] = import_stats.get("rebuild_pool_types", [])
            result["datasets_pending"] = import_stats.get("datasets_pending", 0)
        except Exception as e:
            result["success"] = False
            result["message"] = f"Import failed: {str(e)}"
            return result
        finally:
            session.close()

        # Step 2: 为新增数据集构建物理表（增量模式）
        if result["datasets_pending"] > 0:
            build_resp = self.table_builder.build_all_physical_tables(
                json_path=self.json_path,
                overwrite=False,   # 增量：跳过已存在的表
            )
            result["build_response"] = {
                "tables_created": build_resp.tables_created,
                "tables_skipped": build_resp.tables_skipped,
                "tables_failed": build_resp.tables_failed,
                "errors": build_resp.errors,
            }

        # Step 3: 为属性变更的池类型重建物理表
        if result["rebuild_pool_types"]:
            rebuild_resp = self.table_builder.rebuild_pool_physical_tables(
                pool_types=result["rebuild_pool_types"],
                overwrite=True,
            )
            result["rebuild_response"] = {
                "pool_types_rebuilt": result["rebuild_pool_types"],
                "tables_recreated": rebuild_resp.tables_created,
                "tables_failed": rebuild_resp.tables_failed,
                "errors": rebuild_resp.errors,
            }

        result["message"] = (
            f"Import done: {result['import_stats'].get('datasets', 0)} datasets imported, "
            f"{result.get('datasets_pending', 0)} tables created, "
            f"{len(result['rebuild_pool_types'])} pool types rebuilt"
        )
        return result

    def get_statistics(self) -> DatabaseStats:
        """获取数据库统计信息"""
        return self.table_builder.get_database_stats()

    def backfill_chinese_columns(self) -> Dict[str, int]:
        """
        回填 meta_datasets 中缺失的中文列

        从 meta_work_types / meta_data_categories / meta_data_pools 查中文值，
        填充到 work_type_zh / category_zh / pool_zh 为空的记录。

        Returns:
            各字段的回填统计 {"work_type_zh": N, "category_zh": N, "pool_zh": N}
        """
        return self.table_builder.backfill_missing_chinese()

    def list_tables(
        self,
        pool_type: Optional[str] = None,
        work_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出所有物理数据表

        Args:
            pool_type: 数据池类型过滤
            work_type: 工种过滤

        Returns:
            表列表
        """
        tables = self.table_builder.list_all_physical_tables(pool_type)

        result = []
        for table in tables:
            # 应用工种过滤
            if work_type and table.work_type != work_type:
                continue

            result.append({
                "table_name": table.table_name,
                "work_type": table.work_type,
                "pool_type": table.data_pool,
                "pool_type_zh": SchemaGenerator.get_pool_type_name(table.data_pool or ""),
                "dataset_zh": table.dataset_zh,
                "row_count": table.row_count,
                "column_count": len(table.columns),
                "columns": [
                    {
                        "name": c.name,
                        "type": c.type,
                        "nullable": c.nullable,
                        "comment": c.comment,
                    }
                    for c in table.columns
                ],
            })

        return result

    def get_table_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        获取表结构信息

        Args:
            table_name: 表名

        Returns:
            表结构信息
        """
        info = self.table_builder.get_table_info(table_name)
        if not info:
            return None

        pool_type = info.data_pool or ""

        # 从数据库加载该 pool 的属性模板
        session = self.table_builder.get_session()
        try:
            template = session.query(AttributeTemplateModel).filter_by(pool_type=pool_type).first()
            attrs = template.attributes if template else {}
        finally:
            session.close()

        schema = SchemaGenerator.generate_pool_schema(pool_type, attrs)

        return {
            "table_name": info.table_name,
            "work_type": info.work_type,
            "pool_type": pool_type,
            "pool_type_zh": SchemaGenerator.get_pool_type_name(pool_type),
            "dataset_zh": info.dataset_zh,
            "row_count": info.row_count,
            "columns": schema["columns"],
            "schema_sql": self.table_builder.generate_create_table_sql(table_name, pool_type, attrs),
        }

    def get_dataset_tree(self) -> List[Dict[str, Any]]:
        """
        获取数据集树形结构

        Returns:
            树形结构数据
        """
        session = self.table_builder.get_session()
        try:
            datasets = session.query(DatasetModel).filter(
                DatasetModel.dataset_en.isnot(None)
            ).all()

            dataset_list = [
                {
                    "work_type_en": ds.work_type_en,
                    "work_type_zh": ds.work_type_zh,
                    "category_en": ds.category_en,
                    "category_zh": ds.category_zh,
                    "pool_en": ds.pool_en,
                    "pool_zh": ds.pool_zh,
                    "dataset_en": ds.dataset_en,
                    "dataset_zh": ds.dataset_zh,
                    "table_name": ds.table_name,
                    "physical_table_name": ds.physical_table_name,
                }
                for ds in datasets
            ]

            return SchemaGenerator.generate_dataset_tree(dataset_list)
        finally:
            session.close()

    def export_sql_script(self, output_path: str | Path) -> str:
        """
        导出建表SQL脚本

        Args:
            output_path: 输出文件路径

        Returns:
            SQL脚本内容
        """
        session = self.table_builder.get_session()
        sql_lines = ["-- GenBFKit Database Schema SQL Script", ""]
        sql_lines.append("-- Generated from JSON data")
        sql_lines.append(f"-- Database: {self.db_settings.database}")
        sql_lines.append("")

        try:
            # 一次性加载所有属性模板
            templates = session.query(AttributeTemplateModel).all()
            pool_attrs_map = {t.pool_type: t.attributes for t in templates}

            # 导出所有数据集的建表SQL
            datasets = session.query(DatasetModel).filter(
                DatasetModel.dataset_en.isnot(None),
                DatasetModel.physical_table_name.isnot(None),
            ).all()

            for ds in datasets:
                attrs = pool_attrs_map.get(ds.pool_en, {})
                sql = self.table_builder.generate_create_table_sql(ds.physical_table_name, ds.pool_en, attrs)
                sql_lines.append(f"-- Dataset: {ds.dataset_en} ({ds.dataset_zh})")
                sql_lines.append(sql)
                sql_lines.append("")

            # 导出元数据表创建
            sql_lines.append("-- Metadata Tables")
            sql_lines.append(self._generate_metadata_sql())

        finally:
            session.close()

        sql_content = "\n".join(sql_lines)

        # 写入文件
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sql_content)

        return sql_content

    def _generate_metadata_sql(self) -> str:
        """生成元数据表的SQL"""
        # 简化版本，实际应该从模型定义生成
        return """
-- Metadata Tables (created via SQLAlchemy)
-- These tables are automatically created by the ORM models
"""


# 全局单例
_manager_instance: Optional[DatabaseManager] = None


def get_manager(
    db_settings: Optional[DatabaseSettings] = None,
    json_path: Optional[str | Path] = None,
) -> DatabaseManager:
    """
    获取数据库管理器单例

    Args:
        db_settings: 数据库配置
        json_path: JSON数据文件路径

    Returns:
        DatabaseManager 实例
    """
    global _manager_instance
    if _manager_instance is None or db_settings is not None:
        _manager_instance = DatabaseManager(db_settings, json_path)
    return _manager_instance
