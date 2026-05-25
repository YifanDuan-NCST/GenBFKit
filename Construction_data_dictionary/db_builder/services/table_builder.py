# -*- coding: utf-8 -*-
"""表构建服务 - 从JSON数据全量构建数据库物理表"""

import json
import time
import uuid
import zlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text, inspect, func
from sqlalchemy.dialects.postgresql import dialect as pg_dialect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine

from ..config import DatabaseSettings
from ..models import Base, DatasetModel, DynamicTableRegistry, create_dynamic_table_model, WorkTypeModel, DataCategoryModel, DataPoolModel, AttributeTemplateModel
from ..schemas.database import (
    ColumnInfo,
    TableInfo,
    TableBuildRequest,
    TableBuildResponse,
    BuildProgress,
    PoolTypeStats,
    WorkTypeStats,
    DatabaseStats,
)
from ..services.schema_generator import SchemaGenerator


class TableBuilder:
    """
    数据库表构建器

    核心功能:
    1. 根据JSON数据文件全量构建元数据表 (meta_datasets, meta_work_types 等)
    2. 根据9种数据池类型，为每个Dataset创建独立的物理数据表
    3. 管理表创建进度和状态
    """

    def __init__(self, db_settings: Optional[DatabaseSettings] = None):
        """
        初始化表构建器

        Args:
            db_settings: 数据库配置，默认使用 db_builder.config 中的设置
        """
        from ..config import settings as default_settings
        self.db_settings = db_settings or default_settings.database
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    @property
    def engine(self) -> Engine:
        """获取数据库引擎（懒加载）"""
        if self._engine is None:
            self._engine = create_engine(
                self.db_settings.url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False,
            )
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """获取会话工厂"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def get_session(self) -> Session:
        """获取新的数据库会话"""
        return self.session_factory()

    # ==================== 元数据表管理 ====================

    def init_metadata_tables(self, drop_existing: bool = False) -> bool:
        """
        初始化元数据表

        Args:
            drop_existing: 是否先删除已存在的元数据表（用于重置）

        Returns:
            是否成功
        """
        try:
            with self.engine.begin() as conn:
                if drop_existing:
                    Base.metadata.drop_all(conn)
                    conn.execute(text("DROP TABLE IF EXISTS meta_work_types CASCADE"))
                    conn.execute(text("DROP TABLE IF EXISTS meta_data_categories CASCADE"))
                    conn.execute(text("DROP TABLE IF EXISTS meta_data_pools CASCADE"))
                    conn.execute(text("DROP TABLE IF EXISTS meta_datasets CASCADE"))
                    conn.execute(text("DROP TABLE IF EXISTS meta_attribute_templates CASCADE"))

                # 创建元数据表 (使用 Base.metadata)
                Base.metadata.create_all(
                    conn,
                    tables=[
                        Base.metadata.tables["meta_work_types"],
                        Base.metadata.tables["meta_data_categories"],
                        Base.metadata.tables["meta_data_pools"],
                        Base.metadata.tables["meta_datasets"],
                        Base.metadata.tables["meta_attribute_templates"],
                    ],
                )
            return True
        except Exception as e:
            print(f"Failed to initialize metadata tables: {e}")
            return False

    def drop_metadata_tables(self) -> bool:
        """删除所有元数据表"""
        try:
            Base.metadata.drop_all(self.engine)
            return True
        except Exception as e:
            print(f"Failed to drop metadata tables: {e}")
            return False

    def clear_all_tables(self) -> Tuple[int, int]:
        """
        清空所有表数据（保留表结构）

        Returns:
            (元数据清空数, 动态数据表清空数)
        """
        metadata_deleted = 0
        dynamic_deleted = 0

        session = self.get_session()
        try:
            # 清空元数据表
            for table_name in ["meta_work_types", "meta_data_categories",
                               "meta_data_pools", "meta_datasets", "meta_attribute_templates"]:
                result = session.execute(text(f"DELETE FROM {table_name}"))
                metadata_deleted += result.rowcount

            # 清空所有物理数据表（通过 meta_datasets 获取真实已建表）
            physical_table_names = [
                ds.physical_table_name
                for ds in session.query(DatasetModel.physical_table_name)
                .filter(
                    DatasetModel.physical_table_name.isnot(None),
                    DatasetModel.physical_table_name != "",
                ).all()
            ]

            # 验证表是否存在后再清空
            inspector = inspect(self.engine)
            existing_physical = set(inspector.get_table_names())
            for table_name in physical_table_names:
                if table_name in existing_physical:
                    result = session.execute(text(f'DELETE FROM "{table_name}"'))
                    dynamic_deleted += result.rowcount

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error clearing tables: {e}")
        finally:
            session.close()

        return metadata_deleted, dynamic_deleted

    # ==================== JSON 数据加载 ====================

    def load_json_data(self, json_path: str | Path) -> Dict[str, Any]:
        """
        加载JSON数据文件

        Args:
            json_path: JSON文件路径

        Returns:
            解析后的JSON数据
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def validate_json_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证JSON数据结构

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        required_keys = ["base_work_types", "categories", "pools", "datasets", "attribute_templates"]

        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")

        if "datasets" in data and not isinstance(data["datasets"], list):
            errors.append("'datasets' must be a list")

        if "attribute_templates" in data and not isinstance(data["attribute_templates"], dict):
            errors.append("'attribute_templates' must be a dict")

        return len(errors) == 0, errors

    # ==================== 元数据导入 ====================

    def import_metadata_from_json(
        self,
        data: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        从 JSON 数据导入元数据（幂等增量模式）

        支持：
        1. 新增工种/类别/数据池/数据集
        2. 已存在记录的幂等跳过
        3. 属性模板的 Upsert（新增或属性变更自动触发相关表重建）

        Args:
            data: JSON 数据字典
            session: 可选的数据库会话

        Returns:
            导入统计（含 rebuild_pool_types 列表供调用方处理）
        """
        stats = {
            "work_types": 0,
            "categories": 0,
            "pools": 0,
            "datasets": 0,
            "datasets_pending": 0,    # 新增：待建表的数据集
            "attribute_templates": 0,
            "attribute_templates_updated": 0,
            "attribute_templates_new": 0,
            "rebuild_pool_types": [],  # 属性变更的池类型，需重建其物理表
        }

        close_session = session is None
        session = session or self.get_session()

        try:
            # 导入工种
            existing_wts = {wt.work_type_en for wt in session.query(WorkTypeModel).all()}
            for wt in data.get("base_work_types", []):
                if wt["work_type_en"] not in existing_wts:
                    model = WorkTypeModel(
                        work_type_en=wt["work_type_en"],
                        work_type_zh=wt.get("work_type_zh", ""),
                        no=wt.get("no"),
                    )
                    session.add(model)
                    stats["work_types"] += 1
                    existing_wts.add(wt["work_type_en"])

            # 导入类别
            existing_cats = {(cat.work_type_en, cat.category_en) for cat in session.query(DataCategoryModel).all()}
            for cat in data.get("categories", []):
                key = (cat["work_type_en"], cat["category_en"])
                if key not in existing_cats:
                    model = DataCategoryModel(
                        work_type_en=cat["work_type_en"],
                        work_type_zh=cat.get("work_type_zh", ""),
                        category_en=cat["category_en"],
                        category_zh=cat.get("category_zh", ""),
                    )
                    session.add(model)
                    stats["categories"] += 1
                    existing_cats.add(key)

            # 导入数据池类型
            existing_pools = {(pool.work_type_en, pool.category_en, pool.pool_en) for pool in session.query(DataPoolModel).all()}
            for pool in data.get("pools", []):
                key = (pool.get("work_type_en", ""), pool.get("category_en", ""), pool["pool_en"])
                if key not in existing_pools:
                    model = DataPoolModel(
                        work_type_en=pool.get("work_type_en", ""),
                        work_type_zh=pool.get("work_type_zh", ""),
                        category_en=pool.get("category_en", ""),
                        category_zh=pool.get("category_zh", ""),
                        pool_en=pool["pool_en"],
                        pool_zh=pool.get("pool_zh", ""),
                    )
                    session.add(model)
                    stats["pools"] += 1
                    existing_pools.add(key)

            # 预先加载 lookup 字典（从已导入的表），用于中文翻译回填
            wt_zh_map = {wt.work_type_en: wt.work_type_zh for wt in session.query(WorkTypeModel).all()}
            cat_zh_map = {(cat.work_type_en, cat.category_en): cat.category_zh for cat in session.query(DataCategoryModel).all()}
            # pools 段只有 pool_en/pool_zh，无 work_type/category，故 pool_zh_map 用 pool_en 单键
            pool_zh_map = {pool.pool_en: pool.pool_zh for pool in session.query(DataPoolModel).all()}

            # 导入数据集 - 幂等去重：按唯一键检查
            existing_keys = {
                (ds.work_type_en, ds.category_en, ds.pool_en, ds.dataset_en)
                for ds in session.query(DatasetModel).all()
            }

            for ds in data.get("datasets", []):
                key = (ds["work_type_en"], ds["category_en"], ds["pool_en"], ds["dataset_en"])
                if key in existing_keys:
                    continue

                existing_keys.add(key)
                # table_name = 参数全称（唯一标识），physical_table_name = 物理表简称
                full_name = ds["dataset_en"]
                physical_table = DynamicTableRegistry.generate_table_name(
                    ds["work_type_en"],
                    ds["category_en"],
                    ds["pool_en"],
                    ds["dataset_en"],
                )

                # 优先取 JSON 中的值，空则从 lookup 表回填
                work_type_zh = ds.get("work_type_zh") or wt_zh_map.get(ds["work_type_en"], "")
                category_zh   = ds.get("category_zh")   or cat_zh_map.get((ds["work_type_en"], ds["category_en"]), "")
                pool_zh       = ds.get("pool_zh")       or pool_zh_map.get(ds["pool_en"], "")

                model = DatasetModel(
                    work_type_en=ds["work_type_en"],
                    work_type_zh=work_type_zh,
                    category_en=ds["category_en"],
                    category_zh=category_zh,
                    pool_en=ds["pool_en"],
                    pool_zh=pool_zh,
                    dataset_en=ds["dataset_en"],
                    dataset_zh=ds.get("dataset_zh", ""),
                    dataset_zh_short=ds.get("dataset_zh_short", ""),
                    table_name=full_name,
                    physical_table_name=physical_table,
                    table_created="pending",   # 新增数据集：待建表
                )
                session.add(model)
                stats["datasets"] += 1
                stats["datasets_pending"] += 1

            # 属性模板 Upsert（核心增量支持）
            # 加载已有模板
            existing_templates = {t.pool_type: t for t in session.query(AttributeTemplateModel).all()}

            for pool_type, attrs in data.get("attribute_templates", {}).items():
                if pool_type in existing_templates:
                    # 已存在：比较属性是否变更
                    existing_attrs = existing_templates[pool_type].attributes
                    if existing_attrs != attrs:
                        # 属性有变化 → 更新模板，并标记需重建
                        existing_templates[pool_type].attributes = attrs
                        if pool_type not in stats["rebuild_pool_types"]:
                            stats["rebuild_pool_types"].append(pool_type)
                        stats["attribute_templates_updated"] += 1
                        print(f"[TableBuilder] Attribute template changed for pool type: {pool_type}")
                else:
                    # 新增池类型
                    model = AttributeTemplateModel(pool_type=pool_type, attributes=attrs)
                    session.add(model)
                    if pool_type not in stats["rebuild_pool_types"]:
                        stats["rebuild_pool_types"].append(pool_type)
                    stats["attribute_templates"] += 1
                    stats["attribute_templates_new"] += 1
                    print(f"[TableBuilder] New attribute template for pool type: {pool_type}")

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error importing metadata: {e}")
            raise
        finally:
            if close_session:
                session.close()

        return stats

    def backfill_missing_chinese(self, session: Optional[Session] = None) -> Dict[str, int]:
        """
        回填 meta_datasets 中缺失的中文列

        从 meta_work_types / meta_data_categories / meta_data_pools 查中文值，
        填充到 meta_datasets.work_type_zh / category_zh / pool_zh 为空的记录。

        Args:
            session: 可选的数据库会话

        Returns:
            各字段的回填统计
        """
        stats = {"work_type_zh": 0, "category_zh": 0, "pool_zh": 0}
        close_session = session is None
        session = session or self.get_session()

        try:
            # 预加载 lookup 表
            wt_zh_map = {wt.work_type_en: wt.work_type_zh for wt in session.query(WorkTypeModel).all()}
            cat_zh_map = {
                (cat.work_type_en, cat.category_en): cat.category_zh
                for cat in session.query(DataCategoryModel).all()
            }
            # pools 段只有 pool_en/pool_zh，无 work_type/category，故 pool_zh_map 用 pool_en 单键
            pool_zh_map = {pool.pool_en: pool.pool_zh for pool in session.query(DataPoolModel).all()}

            # 回填 work_type_zh
            datasets = session.query(DatasetModel).filter(
                DatasetModel.work_type_zh.is_(None),
            ).all()
            for ds in datasets:
                zh = wt_zh_map.get(ds.work_type_en)
                if zh:
                    ds.work_type_zh = zh
                    stats["work_type_zh"] += 1

            # 回填 category_zh
            datasets = session.query(DatasetModel).filter(
                DatasetModel.category_zh.is_(None),
            ).all()
            for ds in datasets:
                zh = cat_zh_map.get((ds.work_type_en, ds.category_en))
                if zh:
                    ds.category_zh = zh
                    stats["category_zh"] += 1

            # 回填 pool_zh
            datasets = session.query(DatasetModel).filter(
                DatasetModel.pool_zh.is_(None),
            ).all()
            for ds in datasets:
                zh = pool_zh_map.get(ds.pool_en)
                if zh:
                    ds.pool_zh = zh
                    stats["pool_zh"] += 1

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error backfilling Chinese columns: {e}")
            raise
        finally:
            if close_session:
                session.close()

        return stats

    # ==================== 物理表构建 ====================

    def create_physical_table(
        self,
        session: Session,
        dataset_record: DatasetModel,
        overwrite: bool = False,
    ) -> Tuple[bool, str]:
        """
        为单个Dataset创建物理数据表

        Args:
            session: 数据库会话
            dataset_record: Dataset元数据记录
            overwrite: 是否覆盖已存在的表

        Returns:
            (是否成功, 消息)
        """
        try:
            table_name = dataset_record.physical_table_name
            pool_type = dataset_record.pool_en

            # 检查表是否已存在
            inspector = inspect(self.engine)
            if table_name in inspector.get_table_names():
                if not overwrite:
                    return True, "Table already exists"
                # overwrite=True 时先删除旧表再重建
                with self.engine.begin() as conn:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))

            # 查询该 pool 的属性模板
            attr_template = session.query(AttributeTemplateModel).filter_by(pool_type=pool_type).first()
            attributes = attr_template.attributes if attr_template else {}

            # 创建动态模型（从 meta_attribute_templates 加载属性列）
            DynamicModel = create_dynamic_table_model(
                table_name=table_name,
                pool_type=pool_type,
                dataset_uuid=str(dataset_record.id),
                metadata=Base.metadata,
                attributes=attributes,
            )

            # 创建表
            DynamicModel.__table__.create(self.engine)

            # 回填表创建状态
            dataset_record.table_created = "created"
            session.commit()

            return True, "Success"
        except Exception as e:
            dataset_record.table_created = "failed"
            session.commit()
            return False, str(e)

    def build_all_physical_tables(
        self,
        json_path: str | Path,
        overwrite: bool = False,
        batch_size: int = 100,
        progress_callback: Optional[callable] = None,
    ) -> TableBuildResponse:
        """
        全量构建所有物理数据表（支持增量模式）

        默认增量模式：只处理 table_created='pending' 或不存在的表，
        已创建的表默认跳过，除非指定 overwrite=True。

        Args:
            json_path: JSON数据文件路径
            overwrite: 是否覆盖已存在的表（True 时重建所有表）
            batch_size: 每批处理的表数量
            progress_callback: 进度回调函数

        Returns:
            构建响应
        """
        start_time = time.time()
        response = TableBuildResponse(
            success=True,
            message="",
            tables_created=0,
            tables_skipped=0,
            tables_failed=0,
            errors=[],
            duration_seconds=0.0,
        )

        try:
            # 加载并验证JSON
            data = self.load_json_data(json_path)
            valid, errors = self.validate_json_data(data)
            if not valid:
                response.success = False
                response.message = f"Invalid JSON data: {errors}"
                return response

            # 元数据已在 init_db.py 导入，此处跳过以避免重复
            # （幂等去重确保安全）
            session = self.get_session()
            try:
                # 增量模式：只查询 pending 的数据集（新增未建表的）
                # 加上已建表但 overwrite=True 时也要处理
                if overwrite:
                    datasets = session.query(DatasetModel).filter(
                        DatasetModel.physical_table_name.isnot(None)
                    ).all()
                else:
                    datasets = session.query(DatasetModel).filter(
                        DatasetModel.physical_table_name.isnot(None),
                        DatasetModel.table_created == "pending",  # 只处理新建的
                    ).all()

                total = len(datasets)
                for i, ds in enumerate(datasets):
                    # 检查是否跳过（增量模式默认跳过已存在的）
                    if not overwrite and ds.table_created == "created":
                        response.tables_skipped += 1
                        continue

                    # 创建表
                    success, msg = self.create_physical_table(session, ds, overwrite)

                    if success:
                        response.tables_created += 1
                    else:
                        response.tables_failed += 1
                        response.errors.append(f"{ds.dataset_en}: {msg}")

                    # 进度回调
                    if progress_callback:
                        progress_callback(BuildProgress(
                            total=total,
                            completed=i + 1,
                            failed=response.tables_failed,
                            current_table=ds.physical_table_name,
                            percentage=round((i + 1) / total * 100, 2),
                        ))

                    # 批量提交
                    if (i + 1) % batch_size == 0:
                        session.commit()

                session.commit()
            finally:
                session.close()

        except Exception as e:
            response.success = False
            response.errors.append(f"Build error: {str(e)}")

        response.duration_seconds = round(time.time() - start_time, 2)
        return response

    def rebuild_pool_physical_tables(
        self,
        pool_types: List[str],
        overwrite: bool = True,
        batch_size: int = 100,
        progress_callback: Optional[callable] = None,
    ) -> TableBuildResponse:
        """
        重建指定数据池类型的所有物理表（用于属性模板变更后）

        当某个池类型的属性模板发生变更时，需要重建该池类型下的所有物理表。
        此方法会：
        1. 删除现有物理表
        2. 根据更新后的属性模板重建物理表

        Args:
            pool_types: 需要重建的池类型列表
            overwrite: 必须为 True（删除重建）
            batch_size: 每批处理的表数量
            progress_callback: 进度回调函数

        Returns:
            构建响应
        """
        start_time = time.time()
        response = TableBuildResponse(
            success=True,
            message="",
            tables_created=0,
            tables_skipped=0,
            tables_failed=0,
            errors=[],
            duration_seconds=0.0,
        )

        if not pool_types:
            response.message = "No pool types specified"
            return response

        # 必须覆盖重建
        if not overwrite:
            print("[TableBuilder] rebuild_pool_physical_tables requires overwrite=True, auto-setting to True")
            overwrite = True

        session = self.get_session()
        try:
            # 查询指定池类型的所有数据集
            total_affected = 0
            for pool_type in pool_types:
                datasets = session.query(DatasetModel).filter(
                    DatasetModel.pool_en == pool_type,
                    DatasetModel.physical_table_name.isnot(None),
                ).all()
                total_affected += len(datasets)

                print(f"[TableBuilder] Rebuilding {len(datasets)} tables for pool type: {pool_type}")

                for i, ds in enumerate(datasets):
                    # 删除旧表（使用 overwrite=True 自动触发 DROP）
                    success, msg = self.create_physical_table(session, ds, overwrite=True)

                    if success:
                        response.tables_created += 1
                    else:
                        response.tables_failed += 1
                        response.errors.append(f"{ds.physical_table_name}: {msg}")

                    # 进度回调
                    if progress_callback:
                        progress_callback(BuildProgress(
                            total=total_affected,
                            completed=i + 1,
                            failed=response.tables_failed,
                            current_table=ds.physical_table_name,
                            percentage=round((i + 1) / total_affected * 100, 2),
                        ))

                    # 批量提交
                    if (i + 1) % batch_size == 0:
                        session.commit()

            session.commit()

            # 回填响应消息
            if response.tables_failed > 0:
                response.message = f"Rebuilt {response.tables_created} tables, {response.tables_failed} failed"
            else:
                response.message = f"Successfully rebuilt {response.tables_created} tables for pool types: {pool_types}"

        except Exception as e:
            response.success = False
            response.errors.append(f"Rebuild error: {str(e)}")
        finally:
            session.close()

        response.duration_seconds = round(time.time() - start_time, 2)
        return response

    # ==================== 表信息查询 ====================

    def get_table_info(self, table_name: str) -> Optional[TableInfo]:
        """
        获取表详细信息

        Args:
            table_name: 表名

        Returns:
            表信息，如果不存在返回None
        """
        inspector = inspect(self.engine)

        if table_name not in inspector.get_table_names():
            return None

        columns = []
        for col in inspector.get_columns(table_name):
            columns.append(ColumnInfo(
                name=col["name"],
                type=str(col["type"]),
                nullable=col["nullable"],
                default=col.get("default"),
                comment=col.get("comment"),
            ))

        # 获取行数
        row_count = None
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                row_count = result.scalar()
        except Exception:
            pass

        # 从元数据获取更多信息
        session = self.get_session()
        try:
            dataset = session.query(DatasetModel).filter_by(physical_table_name=table_name).first()
        finally:
            session.close()

        return TableInfo(
            table_name=table_name,
            columns=columns,
            row_count=row_count,
            data_pool=dataset.pool_en if dataset else None,
            dataset_zh=dataset.dataset_zh if dataset else None,
            work_type=dataset.work_type_en if dataset else None,
        )

    def list_all_physical_tables(self, pool_type: Optional[str] = None) -> List[TableInfo]:
        """
        列出所有物理数据表

        通过查询 meta_datasets 表获取已建表的物理表名列表，
        不依赖表名前缀过滤，避免漏掉自定义命名的表。

        Args:
            pool_type: 可选的数据池类型过滤

        Returns:
            表信息列表
        """
        session = self.get_session()
        tables = []
        try:
            # 从 meta_datasets 获取所有已建表的物理表名
            query = session.query(DatasetModel).filter(
                DatasetModel.physical_table_name.isnot(None),
                DatasetModel.physical_table_name != "",
            )
            if pool_type:
                query = query.filter(DatasetModel.pool_en == pool_type)

            dataset_records = query.all()

            for ds in dataset_records:
                table_name = ds.physical_table_name
                # 验证表是否真实存在于数据库
                inspector = inspect(self.engine)
                if table_name not in inspector.get_table_names():
                    continue

                info = self.get_table_info(table_name)
                if info:
                    tables.append(info)
        finally:
            session.close()

        return tables

    def get_database_stats(self) -> DatabaseStats:
        """
        获取数据库统计信息

        Returns:
            数据库统计
        """
        stats = DatabaseStats()

        inspector = inspect(self.engine)
        all_tables = inspector.get_table_names()

        session = self.get_session()
        try:
            # 使用正确的模型进行统计
            stats.total_work_types = session.query(WorkTypeModel).count()
            stats.total_categories = session.query(DataCategoryModel).count()
            stats.total_pools = session.query(DataPoolModel).count()
            stats.total_datasets = session.query(DatasetModel).count()
            stats.total_attribute_templates = session.query(AttributeTemplateModel).count()

            # 物理表统计（从数据库实际表名中获取）
            # 过滤掉 meta_ 和 pg_ 开头的系统表
            physical_tables = [
                t for t in all_tables
                if not t.startswith("meta_") and not t.startswith("pg_")
            ]
            stats.total_tables = len(physical_tables)

            # 计算总记录数
            stats.total_records = 0
            for table_name in physical_tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM \"{table_name}\""))
                    stats.total_records += result.scalar() or 0
                except Exception:
                    pass

            # 数据库大小
            try:
                result = session.execute(text(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                ))
                size_str = result.scalar()
                # 提取数值
                import re
                match = re.search(r'(\d+\.?\d*)\s*([KMGT]?B)', size_str)
                if match:
                    value, unit = float(match.group(1)), match.group(2)
                    multiplier = {"KB": 1/1024, "MB": 1, "GB": 1024, "TB": 1024*1024}.get(unit, 1)
                    stats.database_size_mb = round(value * multiplier, 2)
            except Exception:
                pass

            # 按数据池类型统计（从 meta_datasets 动态获取所有池类型，含自定义）
            all_pool_types = {
                row[0] for row in session.query(DatasetModel.pool_en).distinct().all()
                if row[0]
            }
            for pool_type in sorted(all_pool_types):
                pool_stats = PoolTypeStats(
                    pool_type=pool_type,
                    pool_type_zh=SchemaGenerator.get_pool_type_name(pool_type)
                    if pool_type in SchemaGenerator.POOL_TYPE_NAMES
                    else pool_type,
                )
                pool_datasets = session.query(DatasetModel).filter_by(pool_en=pool_type).all()
                pool_stats.total_tables = len([d for d in pool_datasets if d.physical_table_name])

                # 计算该池类型的总记录数
                table_names_for_pool = [d.physical_table_name for d in pool_datasets if d.physical_table_name]
                pool_stats.total_records = 0
                for t_name in table_names_for_pool:
                    if t_name and t_name in physical_tables:
                        try:
                            result = session.execute(text(f"SELECT COUNT(*) FROM \"{t_name}\""))
                            pool_stats.total_records += result.scalar() or 0
                        except Exception:
                            pass

                stats.pool_types_stats.append(pool_stats)

            # 按工种统计
            work_type_groups = session.query(
                DatasetModel.work_type_en,
                func.count(DatasetModel.id).label("dataset_count")
            ).filter(
                DatasetModel.dataset_en.isnot(None)
            ).group_by(DatasetModel.work_type_en).all()

            for wt_en, dataset_count in work_type_groups:
                wt_model = session.query(WorkTypeModel).filter_by(work_type_en=wt_en).first()

                # 获取该工种下的类别和池数量
                categories_count = session.query(DataCategoryModel).filter_by(work_type_en=wt_en).count()
                pools_count = session.query(DataPoolModel).filter_by(work_type_en=wt_en).count()

                stats.work_types_stats.append(WorkTypeStats(
                    work_type_en=wt_en,
                    work_type_zh=wt_model.work_type_zh if wt_model else None,
                    no=wt_model.no if wt_model else None,
                    datasets=dataset_count,
                    categories=categories_count,
                    pools=pools_count,
                ))

        finally:
            session.close()

        return stats

    def check_database_connection(self) -> Tuple[bool, str]:
        """
        检查数据库连接

        Returns:
            (是否成功, 消息)
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Database connection successful"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    def generate_create_table_sql(
        self,
        table_name: str,
        pool_type: str,
        attributes: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        生成创建表的SQL语句（不实际创建）

        Args:
            table_name: 表名
            pool_type: 数据池类型
            attributes: 属性字典 {attribute_id: attribute_name}，来自 meta_attribute_templates

        Returns:
            CREATE TABLE SQL语句
        """
        if attributes is None:
            attributes = {}

        column_defs = ["id BIGSERIAL PRIMARY KEY"]
        column_defs.append("dataset_id UUID NOT NULL")
        column_defs.append("created_at TIMESTAMP NOT NULL DEFAULT NOW()")

        for attr_id, attr_name in attributes.items():
            name = DynamicTableRegistry.normalize_name(attr_name)
            if name in ("id", "dataset_id", "created_at"):
                name = f"{name}_attr"

            sa_type, nullable, _ = DynamicTableRegistry.infer_column_type(attr_name, attr_id)
            nullable_str = "NOT NULL" if not nullable else ""
            column_defs.append(f"{name} {sa_type} {nullable_str}")

        column_defs.append(f"COMMENT ON TABLE {table_name} IS 'Dataset: {table_name}'")

        sql = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(column_defs) + "\n);"

        # 索引
        table_short = table_name[:40]
        idx_hash_ds = format(zlib.crc32(f"{table_name}_dataset_id".encode()), '04x')
        sql += f"\n\nCREATE INDEX idx_{table_short}{idx_hash_ds}_dataset_id ON {table_name} (dataset_id);"

        return sql
