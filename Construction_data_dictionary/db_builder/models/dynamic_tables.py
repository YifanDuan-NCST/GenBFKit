# -*- coding: utf-8 -*-
"""ORM 动态数据表模型 - 根据数据池类型动态生成"""

import re
import unicodedata
import zlib
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, BigInteger, Boolean, DateTime, Integer, Numeric, String, Text, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class DynamicTableRegistry:
    """
    动态表注册表 - 管理所有动态创建的表模型

    表结构:
    - id: BigInteger, PK, 自增（系统列）
    - dataset_id: UUID, 外键指向 meta_datasets（系统列）
    - {attribute_name}: 来自 meta_attribute_templates 的每个属性（动态列）
    - created_at: DateTime, 创建时间（系统列）
    """

    # 保留字列表 (PostgreSQL 保留关键字)
    RESERVED_WORDS = {
        "all", "analyse", "analyze", "and", "any", "array", "as", "asc",
        "asymmetric", "authorization", "between", "binary", "both", "case",
        "cast", "check", "collate", "collation", "column", "concurrently",
        "constraint", "create", "cross", "current_catalog", "current_date",
        "current_role", "current_schema", "current_time", "current_timestamp",
        "current_user", "default", "deferrable", "desc", "distinct", "do",
        "else", "end", "except", "false", "fetch", "for", "foreign", "from",
        "full", "grant", "group", "having", "ilike", "in", "initially",
        "inner", "intersect", "into", "is", "isnull", "join", "lateral",
        "leading", "left", "like", "limit", "localtime", "localtimestamp",
        "natural", "not", "notnull", "null", "offset", "on", "only",
        "or", "order", "outer", "overlaps", "placing", "primary",
        "references", "returning", "right", "select", "session_user",
        "similar", "some", "symmetric", "table", "tablesample", "then",
        "to", "trailing", "true", "union", "unique", "user", "using",
        "variadic", "verbose", "when", "where", "window", "with",
    }

    # 动态模型缓存，避免重复创建
    _model_cache: Dict[str, type] = {}

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """
        将任意名称规范化为PostgreSQL安全的表名/列名

        规则:
        1. Unicode NFD 归一化（消除全角/半角、上标/下标差异，如 ℃→°）
        2. 转小写
        3. 空格、&、#、- 等替换为下划线
        4. 连续下划线合并
        5. 首尾下划线去除
        6. 若以数字开头则加前缀
        7. 若为保留字则加后缀
        """
        if not name:
            return "unnamed"

        # Unicode NFD 归一化，消除全角/半角、上标/下标差异
        result = unicodedata.normalize('NFD', name)
        # 去除组合附加符号（Mark 类别：Mn/Mc/Me），保留基本字符
        result = ''.join(ch for ch in result if not unicodedata.category(ch).startswith('M'))
        # 转小写并替换特殊字符
        result = name.lower()
        result = re.sub(r'[\s&%#\-\.\/\\]+', '_', result)
        result = re.sub(r'[()（）\[\]「」『』〈〉《》【】{}]', '_', result)
        result = re.sub(r'[_]+', '_', result)
        result = result.strip('_')

        # 若以数字开头，加前缀
        if result and result[0].isdigit():
            result = 't_' + result

        # 若为保留字，加后缀
        if result in cls.RESERVED_WORDS:
            result = result + '_col'

        # 最大长度限制 (PostgreSQL标识符最大63字符)
        if len(result) > 50:
            result = result[:50].rstrip('_')

        return result

    @classmethod
    def generate_table_name(
        cls,
        work_type: str,
        category: str,
        pool: str,
        dataset: str,
    ) -> str:
        """
        生成物理表名

        格式: {work_type}_{category}_{pool}_{dataset}
        全部使用下划线分隔，每个部分都是规范化后的安全名称
        """
        wt = cls.normalize_name(work_type)
        cat = cls.normalize_name(category)
        pl = cls.normalize_name(pool)
        ds = cls.normalize_name(dataset)

        # 合并成一个表名
        full_name = f"{wt}_{cat}_{pl}_{ds}"

        # PostgreSQL 表名最大 63 字符
        if len(full_name) > 63:
            # 截断各部分以控制长度，hash 用原始名称保证唯一性
            parts = [wt, cat, pl, ds]
            max_part_len = (63 - 3 - 5) // 4  # 3个下划线 + 5位hash
            truncated = [p[:max_part_len] if len(p) > max_part_len else p for p in parts]
            base = "_".join(truncated)
            # hash 基于原始名称（保留数字等区分信息），normalize_name 丢失了这些信息
            raw_full = f"{work_type}_{category}_{pool}_{dataset}"
            hash_suffix = format(zlib.crc32(raw_full.encode()), '05x')[-5:]
            full_name = f"{base}_{hash_suffix}"

        return full_name

    @classmethod
    def infer_column_type(cls, attr_name: str, attr_id: str) -> tuple:
        """
        根据属性名称推断列类型

        Returns:
            (SQLAlchemy TypeEngine, nullable: bool, default: Optional[str])
        """
        name_lower = attr_name.lower()

        # 时间戳类属性
        if any(kw in name_lower for kw in ['time', 'timestamp', '时间', '日期']):
            return DateTime, False, None

        # 数值类属性
        if any(kw in name_lower for kw in [
            'value', 'mean', 'average', 'threshold', 'limit', 'range',
            'frequency', 'interval', 'duration', 'period', 'cycle',
            'deviation', 'quantile', 'latency', 'delay', 'ratio', 'rate',
            'score', 'upper', 'lower', 'min', 'max', '标准', '阈值', '周期'
        ]):
            return Numeric(18, 4), True, None

        # 布尔/状态类属性
        if any(kw in name_lower for kw in [
            'status', 'state', 'flag', 'enabled', 'valid', 'available',
            'mapped', 'triggered', 'aligned', 'async',
            'is_', 'has_', 'can_', '状态', '有效', '触发'
        ]):
            return Boolean, True, None

        # JSONB 属性（标签、关键词集等）
        if any(kw in name_lower for kw in [
            'label', 'keyword', 'tag', 'mapping', 'set', '规则'
        ]):
            return JSONB, True, None

        # 整数类（计数器、优先级等）
        if any(kw in name_lower for kw in [
            'count', 'number', 'priority', 'level', 'threshold', 'index',
            '优先级', '序号', '计数'
        ]):
            return Integer, True, None

        # 默认：字符串
        return String(500), True, None


def create_dynamic_table_model(
    table_name: str,
    pool_type: str,
    dataset_uuid: str,
    metadata: Base.metadata,
    attributes: Optional[Dict[str, str]] = None,
) -> type:
    """
    根据数据池类型动态创建SQLAlchemy模型类

    表结构:
    - id: BigInteger, PK, 自增（系统列）
    - dataset_id: UUID, FK -> meta_datasets.id（系统列）
    - {attribute_name}: 来自 meta_attribute_templates（动态列）
    - created_at: DateTime（系统列）

    Args:
        table_name: 物理表名
        pool_type: 数据池类型
        dataset_uuid: 对应数据集的UUID
        metadata: SQLAlchemy MetaData对象
        attributes: 属性字典 {attribute_id: attribute_name}，来自 meta_attribute_templates

    Returns:
        SQLAlchemy模型类
    """
    cache_key = f"{table_name}_{pool_type}"
    if cache_key in DynamicTableRegistry._model_cache:
        return DynamicTableRegistry._model_cache[cache_key]

    # 系统列
    id_col = Column(BigInteger, primary_key=True, autoincrement=True)
    dataset_id_col = Column("dataset_id", UUID(as_uuid=True), nullable=False)
    created_at_col = Column(DateTime, server_default=func.now(), nullable=False)

    model_attrs: Dict[str, Any] = {
        "__tablename__": table_name,
        "id": id_col,
        "dataset_id": dataset_id_col,
        "created_at": created_at_col,
    }

    # 收集所有列用于索引
    all_columns = [id_col, dataset_id_col, created_at_col]
    timestamp_col = None
    idx_columns = []

    # 动态属性列
    if attributes:
        for attr_id, attr_name in attributes.items():
            col_name = DynamicTableRegistry.normalize_name(attr_name)
            # 防止与系统列重名
            if col_name in model_attrs:
                col_name = f"{col_name}_attr"

            sa_type, nullable, default = DynamicTableRegistry.infer_column_type(attr_name, attr_id)
            kwargs = {"nullable": nullable}
            if default:
                kwargs["server_default"] = default

            col = Column(col_name, sa_type, **kwargs)
            model_attrs[col_name] = col
            all_columns.append(col)

            # 记录 timestamp 列用于建索引
            if 'time' in col_name.lower() or 'timestamp' in col_name.lower():
                if timestamp_col is None:
                    timestamp_col = col

    # 索引: dataset_id 必建；timestamp 若存在则建
    table_short = table_name[:40]
    idx_hash_ds = format(zlib.crc32(f"{table_name}_dataset_id".encode()), '04x')
    indexes = [
        Index(f"idx_{table_short}{idx_hash_ds}_dataset_id", dataset_id_col),
    ]
    if timestamp_col is not None:
        idx_hash_ts = format(zlib.crc32(f"{table_name}_timestamp".encode()), '04x')
        indexes.append(Index(f"idx_{table_short}{idx_hash_ts}_timestamp", timestamp_col))

    model_attrs["__table_args__"] = tuple(indexes)

    # 使用 type() 动态创建类
    DynamicModel = type(f"Dynamic_{table_name}", (Base,), model_attrs)

    # 缓存模型
    DynamicTableRegistry._model_cache[cache_key] = DynamicModel

    return DynamicModel
