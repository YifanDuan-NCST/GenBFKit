# -*- coding: utf-8 -*-
"""
Mock Data Generator - 核心生成引擎
"""

import random
import uuid
import time
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

from ..config import DatabaseSettings, settings
from ..services.table_builder import TableBuilder
from ..models import DatasetModel, AttributeTemplateModel


# ============================================================
# 数据池领域词汇库（高炉炼铁行业）
# ============================================================

BLAST_FURNACE_TERMS = {
    # 工种
    "work_types": [
        "IronmakingOperator", "SteelmakingOperator", "MaintenanceOperator",
        "QualityInspector", "ProcessEngineer", "EquipmentEngineer",
        "SafetySupervisor", "ProductionScheduler", "MaterialsEngineer",
        "AutomationEngineer"
    ],
    # 操作动作
    "actions": [
        "blow", "tap", "injection", "charging", "slagging",
        "cooling", "heating", "flowing", "sampling", "measuring",
        "adjusting", "monitoring", "controlling", "loading", "unloading"
    ],
    # 设备
    "equipment": [
        "BF_1", "BF_2", "BF_3", "HotBlastStove", "DustCatcher",
        "GasCleaner", "SlagGranulator", "HotMetalCar", "TorpedoCar",
        "Casthouse", "Taphole", "Tuyere", "Hearth", "Bosh"
    ],
    # 状态
    "states": [
        "normal", "abnormal", "warning", "alarm", "standby",
        "running", "stopped", "maintenance", "fault", "idle"
    ],
    # 材料
    "materials": [
        "sinter", "pellet", "lump_ore", "coke", "pulverized_coal",
        "limestone", "dolomite", "quartzite", "recycled_iron",
        "hot_metal", "pig_iron", "slag", "flue_dust"
    ],
    # 气体
    "gases": [
        "blast_furnace_gas", "top_gas", "reducing_gas", "CO", "CO2",
        "H2", "N2", "O2", "natural_gas", "steam"
    ],
    # 质量等级
    "quality_grades": ["A", "B", "C", "D", "premium", "standard", "substandard"],
    # 警报级别
    "alarm_levels": ["INFO", "WARNING", "CRITICAL", "EMERGENCY"],
    # 位置
    "locations": [
        "bosh", "hearth", "crucible", "tuyere_zone", "dead_man",
        "stock_column", "wall_lining", "bottom", "taphole_area"
    ],
    # 工艺参数前缀
    "param_prefixes": [
        "temp", "pressure", "flow", "level", "velocity",
        "composition", "ratio", "index", "rate", "value"
    ],
}


# ============================================================
# Faker 风格的随机数据生成器
# ============================================================

class DataFaker:
    """行业感十足的随机数据生成器"""

    _random = random.Random()

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            self._random = random.Random(seed)

    def seed(self, seed: int):
        self._random = random.Random(seed)

    # ---- 基础数值类型 ----

    def float_range(self, min_val: float, max_val: float, decimals: int = 4) -> float:
        """指定范围的浮点数"""
        val = self._random.uniform(min_val, max_val)
        return round(val, decimals)

    def int_range(self, min_val: int, max_val: int) -> int:
        """指定范围的整数"""
        return self._random.randint(min_val, max_val)

    def boolean(self) -> bool:
        return self._random.choice([True, False])

    # ---- 高炉行业数据 ----

    def temperature(self, zone: str = "general") -> float:
        """高炉各区域温度 (°C)"""
        zones = {
            "hearth": (1400, 1550),
            "bosh": (1200, 1450),
            "tuyere": (2000, 2400),
            " tuyere_zone": (1800, 2200),
            "stock_top": (100, 400),
            "wall": (200, 800),
            "gas": (800, 1200),
            "general": (500, 2000),
        }
        lo, hi = zones.get(zone, (500, 2000))
        return self.float_range(lo, hi, 2)

    def pressure(self, zone: str = "general") -> float:
        """高炉各区域压力 (kPa / bar)"""
        zones = {
            "hearth": (100, 250),
            "bosh": (200, 450),
            " tuyere_blast": (150, 500),
            "top_gas": (50, 250),
            "cold_blast": (100, 400),
            "hot_blast": (200, 600),
            "general": (50, 600),
        }
        lo, hi = zones.get(zone, (50, 600))
        return self.float_range(lo, hi, 2)

    def flow_rate(self, medium: str = "gas") -> float:
        """流量 (Nm³/h 或 m³/h)"""
        ranges = {
            "blast": (150000, 300000),
            "hot_blast": (150000, 300000),
            "top_gas": (100000, 200000),
            "flue_gas": (50000, 150000),
            "steam": (500, 5000),
            "cooling_water": (50, 500),
            "slag": (5, 50),
            "hot_metal": (10, 100),
            "gas": (100000, 200000),
        }
        lo, hi = ranges.get(medium, (100, 10000))
        return self.float_range(lo, hi, 1)

    def composition(self, component: str = "Fe") -> float:
        """成分分析 (%)"""
        components = {
            "Fe": (55.0, 70.0),
            "Si": (0.1, 1.5),
            "Mn": (0.1, 1.0),
            "P": (0.05, 0.3),
            "S": (0.01, 0.1),
            "C": (2.0, 5.0),
            "Ti": (0.05, 0.3),
            "V": (0.05, 0.3),
            "Al2O3": (5.0, 15.0),
            "CaO": (20.0, 45.0),
            "MgO": (5.0, 15.0),
            "SiO2": (20.0, 40.0),
            "CO": (15.0, 30.0),
            "CO2": (10.0, 25.0),
            "H2": (1.0, 8.0),
        }
        lo, hi = components.get(component, (0.0, 100.0))
        return self.float_range(lo, hi, 4)

    def ratio_value(self) -> float:
        """比值类参数 (如 风焦比 等)"""
        return self.float_range(0.1, 10.0, 3)

    def index_value(self, base: float = 100.0) -> float:
        """指数/索引值"""
        return self.float_range(base * 0.7, base * 1.3, 2)

    def level_value(self) -> float:
        """料位/液位 (mm)"""
        return self.float_range(0.0, 10000.0, 1)

    def velocity(self) -> float:
        """速度 (m/s)"""
        return self.float_range(0.0, 50.0, 3)

    def weight(self) -> float:
        """重量 (kg / t)"""
        return self.float_range(0.0, 500.0, 2)

    # ---- 时间类型 ----

    def timestamp(self,
                  start: Optional[datetime] = None,
                  end: Optional[datetime] = None) -> datetime:
        """随机时间戳"""
        if start is None:
            start = datetime(2024, 1, 1)
        if end is None:
            end = datetime(2025, 12, 31)
        delta = (end - start).total_seconds()
        offset = self._random.uniform(0, delta)
        return start + timedelta(seconds=offset)

    def duration(self, max_hours: int = 168) -> float:
        """持续时间 (小时)"""
        return self.float_range(0.0, max_hours, 2)

    def interval(self) -> float:
        """间隔时间 (秒)"""
        return self.float_range(0.1, 3600.0, 1)

    # ---- 文本类型 ----

    def enum_value(self, options: List[str]) -> str:
        """枚举值（从给定列表选择）"""
        if not options:
            return "unknown"
        return self._random.choice(options)

    def text_snippet(self, min_words: int = 5, max_words: int = 30) -> str:
        """文本片段"""
        words = []
        for _ in range(self._random.randint(min_words, max_words)):
            words.append(self._random.choice([
                "parameter", "adjustment", "reading", "value", "reading",
                "recorded", "measured", "observed", "analyzed", "controlled",
                "monitored", "optimized", "improved", "stable", "nominal",
                "actual", "target", "expected", "deviation", "within", "range"
            ]))
        return " ".join(words)

    def batch_id(self) -> str:
        """批次号"""
        date = self.timestamp().strftime("%Y%m%d")
        seq = self._random.randint(1, 9999)
        return f"BATCH_{date}_{seq:04d}"

    def heat_id(self) -> str:
        """炉次号"""
        date = self.timestamp().strftime("%Y%m%d")
        seq = self._random.randint(1, 999)
        return f"HEAT_{date}_{seq:03d}"

    def equipment_id(self) -> str:
        """设备编号"""
        return self._random.choice(BLAST_FURNACE_TERMS["equipment"])

    def location_code(self) -> str:
        """位置编码"""
        return self._random.choice(BLAST_FURNACE_TERMS["locations"])

    # ---- JSONB 类型 ----

    def tags(self, max_tags: int = 5) -> List[str]:
        """标签列表"""
        pool = [
            "critical", "monitored", "optimized", "historical",
            "real-time", "batch", "continuous", "triggered",
            "manual", "automatic", "predicted", "measured"
        ]
        return self._random.sample(pool, k=min(self._random.randint(1, max_tags), len(pool)))

    def keywords(self, max_kw: int = 6) -> List[str]:
        """关键词列表"""
        pool = [
            "blast_furnace", "ironmaking", "hot_metal", "slag",
            "reduction", "coke", "sinter", "pellet", "raw_materials",
            "gas_analysis", "temperature_control", "pressure_control",
            "burden_distribution", "tuyere_injection", "PCI"
        ]
        return self._random.sample(pool, k=min(self._random.randint(1, max_kw), len(pool)))

    def mapping_data(self) -> Dict[str, Any]:
        """映射数据 (JSON)"""
        return {
            "source": self._random.choice(["sensor", "DCS", "manual", "L2", "L3"]),
            "quality": self._random.choice(["good", "uncertain", "bad"]),
            "unit": self._random.choice(["°C", "kPa", "Nm3/h", "%", "kg"]),
            "accuracy": round(self._random.uniform(0.1, 5.0), 2),
        }

    def rule_set(self) -> Dict[str, Any]:
        """规则集 (JSON)"""
        return {
            "min": round(self._random.uniform(0, 100), 2),
            "max": round(self._random.uniform(100, 1000), 2),
            "target": round(self._random.uniform(100, 900), 2),
            "tolerance": round(self._random.uniform(0.1, 10.0), 2),
            "enabled": self.boolean(),
        }


# ============================================================
# 列类型 → 数据生成器映射
# ============================================================

class ColumnTypeMapper:
    """
    根据列名 + 列类型自动选择最合适的虚拟数据生成策略。
    这是生成真实感行业数据的关键。
    """

    def __init__(self, faker: DataFaker):
        self.faker = faker

    def infer_from_name(self, col_name: str, col_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        根据列名 + 列类型推断最合适的数据生成策略。
        PostgreSQL 实际列类型优先级最高，列名关键词作为辅助参考。

        Returns:
            (generator_type, kwargs)
        """
        name = col_name.lower()
        pg_type = col_type.lower()

        # =====================================================
        # Step 1: PostgreSQL 列类型优先级判断（最可靠）
        # =====================================================
        if any(kw in pg_type for kw in ["bool"]):
            return "boolean", {}
        if any(kw in pg_type for kw in ["int", "serial"]):
            return "counter", {}
        if any(kw in pg_type for kw in ["numeric", "decimal", "real", "double", "float"]):
            return "numeric", {}
        if any(kw in pg_type for kw in ["date", "time"]) and "timestamp" not in pg_type:
            return "timestamp", {}
        if "timestamp" in pg_type:
            return "timestamp", {}
        if "json" in pg_type:
            return "tags", {}

        # =====================================================
        # Step 2: 列名关键词推断（辅助调整生成数据范围）
        # 列名推断只决定内容域，不改变基本类型
        # =====================================================
        if any(kw in name for kw in ["time", "timestamp", "datetime", "date"]):
            return "timestamp", {}

        if any(kw in name for kw in ["duration", "持续"]):
            return "duration", {}

        if any(kw in name for kw in ["interval", "间隔"]):
            return "interval", {}

        # ---- 温度类 ----
        if any(kw in name for kw in ["temp", "temperature", "温度"]):
            # 识别温度区域
            zone = "general"
            if any(z in name for z in ["hearth", "炉缸", "缸底"]):
                zone = "hearth"
            elif any(z in name for z in ["bosh", "炉腹", "炉腰"]):
                zone = "bosh"
            elif any(z in name for z in ["tuyere", "风口", "热风"]):
                zone = "tuyere"
            elif any(z in name for z in ["top", "炉顶", "料线"]):
                zone = "stock_top"
            elif any(z in name for z in ["wall", "炉墙", "炉壁"]):
                zone = "wall"
            elif any(z in name for z in ["gas", "煤气"]):
                zone = "gas"
            return "temperature", {"zone": zone}

        # ---- 压力类 ----
        if any(kw in name for kw in ["pressure", "press", "压"]):
            zone = "general"
            if any(z in name for z in ["blast", "风压", "热风"]):
                zone = " tuyere_blast" if "hot" in name else " tuyere_blast"
                zone = "hot_blast" if "hot" in name else " tuyere_blast"
            elif any(z in name for z in ["top", "炉顶"]):
                zone = "top_gas"
            elif any(z in name for z in ["hearth", "炉缸"]):
                zone = "hearth"
            return "pressure", {"zone": zone}

        # ---- 流量类 ----
        if any(kw in name for kw in ["flow", "flux", "流量", "风量", "煤气量"]):
            medium = "gas"
            if any(z in name for z in ["blast", "风"]):
                medium = "blast"
            elif any(z in name for z in ["hot", "热风"]):
                medium = "hot_blast"
            elif any(z in name for z in ["top", "炉顶", "荒"]):
                medium = "top_gas"
            elif any(z in name for z in ["flue", "烟"]):
                medium = "flue_gas"
            elif any(z in name for z in ["steam", "蒸汽"]):
                medium = "steam"
            elif any(z in name for z in ["water", "冷却", "水"]):
                medium = "cooling_water"
            elif any(z in name for z in ["slag", "渣"]):
                medium = "slag"
            elif any(z in name for z in ["metal", "铁", "hot_metal"]):
                medium = "hot_metal"
            return "flow_rate", {"medium": medium}

        # ---- 成分分析 ----
        if any(kw in name for kw in [
            "composition", "content", "component", "element",
            "成分", "含量", "元素", "组分"
        ]):
            # 从列名中提取成分
            for comp in ["Fe", "Si", "Mn", "P", "S", "C", "Ti", "V",
                         "Al2O3", "CaO", "MgO", "SiO2", "CO", "CO2", "H2"]:
                if comp.lower() in name:
                    return "composition", {"component": comp}
            return "composition", {"component": "Fe"}

        # ---- 数值类 ----
        if any(kw in name for kw in [
            "value", "mean", "average", "avg", "标准", "偏差",
            "threshold", "limit", "range", "min", "max",
            "deviation", "quantile", "latency", "delay",
            "ratio", "rate", "score", "index", "index_value",
            "upper", "lower", "cycle", "frequency", "period"
        ]):
            # 判断子类型
            if "ratio" in name or "比" in name:
                return "ratio", {}
            if "index" in name or "指标" in name:
                return "index_val", {}
            if "level" in name or "位" in name:
                return "level", {}
            if "velocity" in name or "速度" in name:
                return "velocity", {}
            if "weight" in name or "重" in name or "量" in name:
                return "weight", {}
            if "frequency" in name or "频" in name:
                return "int_range", {"min": 0, "max": 100}
            if "cycle" in name or "周" in name:
                return "int_range", {"min": 1, "max": 1000}
            return "numeric", {}

        # ---- 计数器/序号 ----
        if any(kw in name for kw in [
            "count", "number", "no", "seq", "priority",
            "level", "index", "order", "序号", "计数"
        ]):
            return "counter", {}

        # ---- 布尔/状态类 ----
        if any(kw in name for kw in [
            "status", "state", "flag", "enabled", "valid", "available",
            "is_", "has_", "can_", "trigger", "aligned", "async",
            "状态", "有效", "触发", "使能", "可用", "完成"
        ]):
            return "boolean", {}

        # ---- 枚举/类型 ----
        if any(kw in name for kw in ["type", "kind", "grade", "rank", "class", "类", "级", "等", "型"]):
            return "enum", {"options": ["A", "B", "C", "D"]}

        # ---- 批次/编号 ----
        if any(kw in name for kw in ["batch", "lot", "批次", "批号"]):
            return "batch_id", {}
        if any(kw in name for kw in ["heat", "炉次"]):
            return "heat_id", {}
        if any(kw in name for kw in ["equipment", "device", "设备", "编号"]):
            return "equipment_id", {}

        # ---- 位置 ----
        if any(kw in name for kw in ["location", "position", "zone", "area", "位置", "区域"]):
            return "location", {}

        # ---- JSONB 标签/关键词 ----
        if any(kw in name for kw in ["tag", "标签"]):
            return "tags", {}
        if any(kw in name for kw in ["keyword", "关键词"]):
            return "keywords", {}
        if any(kw in name for kw in ["mapping", "映射"]):
            return "mapping", {}
        if any(kw in name for kw in ["rule", "规则", "threshold"]):
            return "rule_set", {}

        # ---- 默认 ----
        # 根据 PostgreSQL 列类型推断
        if "bool" in col_type.lower():
            return "boolean", {}
        if any(t in col_type.lower() for t in ["int", "serial"]):
            return "counter", {}
        if any(t in col_type.lower() for t in ["numeric", "decimal", "real", "double"]):
            return "numeric", {}
        if "json" in col_type.lower():
            return "tags", {}

        return "text", {}

    def generate(self, col_name: str, col_type: str) -> Any:
        """根据推断结果生成数据"""
        gen_type, kwargs = self.infer_from_name(col_name, col_type)

        if gen_type == "timestamp":
            return self.faker.timestamp()
        elif gen_type == "duration":
            return self.faker.duration()
        elif gen_type == "interval":
            return self.faker.interval()
        elif gen_type == "temperature":
            return self.faker.temperature(kwargs.get("zone", "general"))
        elif gen_type == "pressure":
            return self.faker.pressure(kwargs.get("zone", "general"))
        elif gen_type == "flow_rate":
            return self.faker.flow_rate(kwargs.get("medium", "gas"))
        elif gen_type == "composition":
            return self.faker.composition(kwargs.get("component", "Fe"))
        elif gen_type == "numeric":
            return self.faker.float_range(0.0, 1000.0, 4)
        elif gen_type == "ratio":
            return self.faker.ratio_value()
        elif gen_type == "index_val":
            return self.faker.index_value()
        elif gen_type == "level":
            return self.faker.level_value()
        elif gen_type == "velocity":
            return self.faker.velocity()
        elif gen_type == "weight":
            return self.faker.weight()
        elif gen_type == "counter":
            return self.faker.int_range(0, 10000)
        elif gen_type == "boolean":
            return self.faker.boolean()
        elif gen_type == "enum":
            return self.faker.enum_value(kwargs.get("options", ["A", "B", "C"]))
        elif gen_type == "batch_id":
            return self.faker.batch_id()
        elif gen_type == "heat_id":
            return self.faker.heat_id()
        elif gen_type == "equipment_id":
            return self.faker.equipment_id()
        elif gen_type == "location":
            return self.faker.location_code()
        elif gen_type == "tags":
            return json.dumps(self.faker.tags())
        elif gen_type == "keywords":
            return json.dumps(self.faker.keywords())
        elif gen_type == "mapping":
            return json.dumps(self.faker.mapping_data())
        elif gen_type == "rule_set":
            return json.dumps(self.faker.rule_set())
        elif gen_type == "text":
            return self.faker.text_snippet()
        else:
            return None


# ============================================================
# 核心 Mock 数据生成器
# ============================================================

@dataclass
class GenerationStats:
    """生成统计"""
    total_tables: int = 0
    tables_with_data: int = 0
    tables_skipped: int = 0
    tables_failed: int = 0
    total_rows_generated: int = 0
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tables": self.total_tables,
            "tables_with_data": self.tables_with_data,
            "tables_skipped": self.tables_skipped,
            "tables_failed": self.tables_failed,
            "total_rows_generated": self.total_rows_generated,
            "errors": self.errors,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class MockDataGenerator:
    """
    虚拟数据生成器

    核心功能:
    1. 读取数据库中所有物理表的列信息
    2. 根据列名和列类型智能生成真实感的高炉炼铁行业数据
    3. 将生成的虚拟数据批量插入到对应表中
    4. 支持增量（已满100行跳过）和全量（覆盖）两种模式
    5. 提供详细的生成报告和日志追踪
    """

    def __init__(
        self,
        db_settings: Optional[DatabaseSettings] = None,
        rows_per_table: int = 100,
        seed: Optional[int] = None,
    ):
        """
        Args:
            db_settings: 数据库配置
            rows_per_table: 每个物理表生成的行数
            seed: 随机数种子（用于可复现的测试数据）
        """
        self.db_settings = db_settings or settings.database
        self.rows_per_table = rows_per_table
        self.faker = DataFaker(seed=seed)
        self.mapper = ColumnTypeMapper(self.faker)
        self.table_builder = TableBuilder(self.db_settings)
        self.stats = GenerationStats()

    # ---- 表/列信息读取 ----

    def get_all_physical_tables(self) -> List[str]:
        """获取所有物理表名（排除系统表）"""
        inspector = inspect(self.table_builder.engine)
        all_tables = inspector.get_table_names()
        return [
            t for t in all_tables
            if not t.startswith("meta_") and not t.startswith("pg_")
        ]

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        inspector = inspect(self.table_builder.engine)
        columns = inspector.get_columns(table_name)
        return [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "default": col.get("default"),
            }
            for col in columns
        ]

    def get_existing_row_count(self, table_name: str) -> int:
        """获取表中已有行数"""
        try:
            with self.table_builder.engine.connect() as conn:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                return result.scalar() or 0
        except Exception:
            return 0

    def get_dataset_uuid(self, table_name: str) -> Optional[str]:
        """从 meta_datasets 获取该表对应的 dataset_id"""
        session = self.table_builder.get_session()
        try:
            ds = session.query(DatasetModel).filter_by(
                physical_table_name=table_name
            ).first()
            return str(ds.id) if ds else None
        finally:
            session.close()

    # ---- 数据生成核心 ----

    def _build_insert_sql(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
        row_count: int,
        dataset_uuid: Optional[str],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        构建批量插入 SQL 和数据参数列表。

        SQLAlchemy 2.x 要求 text() 的 executemany 传入 list[dict]。

        Returns:
            (sql_statement, parameters_list)
        """
        # 系统列
        system_cols = ["id", "dataset_id", "created_at"]
        data_cols = [c for c in columns if c["name"] not in system_cols]

        # SQL 列名 + named 参数占位符
        col_names = [c["name"] for c in columns if c["name"] != "id"]
        placeholders = ", ".join([f":{name}" for name in col_names])
        sql = f'INSERT INTO "{table_name}" ({", ".join(col_names)}) VALUES ({placeholders})'

        # 生成所有行（dict 格式，供 SQLAlchemy 2.x text() executemany 使用）
        rows = []
        for _ in range(row_count):
            row_dict = {}
            for col in columns:
                name = col["name"]
                if name == "id":
                    continue  # PostgreSQL auto-increment
                elif name == "dataset_id":
                    row_dict[name] = uuid.UUID(dataset_uuid) if dataset_uuid else uuid.uuid4()
                elif name == "created_at":
                    row_dict[name] = datetime.now()
                else:
                    row_dict[name] = self.mapper.generate(name, col["type"])
            rows.append(row_dict)

        return sql, rows

    def generate_for_table(
        self,
        table_name: str,
        mode: str = "upsert",
        batch_size: int = 500,
    ) -> Dict[str, Any]:
        """
        为单个物理表生成虚拟数据。

        Args:
            table_name: 物理表名
            mode: "upsert"（已有满100行则跳过）| "overwrite"（先清空再插入）
            batch_size: 每批插入的行数

        Returns:
            生成结果 {"success": bool, "rows_inserted": int, "error": str}
        """
        result = {"success": False, "rows_inserted": 0, "error": None}

        try:
            # 1. 获取列信息
            columns = self.get_table_columns(table_name)
            if not columns:
                result["error"] = "表无列信息"
                return result

            # 2. 检查/获取 dataset_uuid
            dataset_uuid = self.get_dataset_uuid(table_name)

            # 3. 检查已有行数
            existing = self.get_existing_row_count(table_name)
            if mode == "upsert" and existing >= self.rows_per_table:
                result["success"] = True
                result["rows_inserted"] = 0
                return result

            # 4. 计算需要插入的行数
            if mode == "upsert":
                rows_to_insert = max(0, self.rows_per_table - existing)
            else:
                rows_to_insert = self.rows_per_table

            if rows_to_insert == 0:
                result["success"] = True
                result["rows_inserted"] = 0
                return result

            # 5. 构建插入SQL
            sql, rows = self._build_insert_sql(
                table_name, columns, rows_to_insert, dataset_uuid
            )

            # 6. 批量执行插入
            with self.table_builder.engine.begin() as conn:
                for i in range(0, len(rows), batch_size):
                    batch = rows[i : i + batch_size]
                    conn.execute(text(sql), batch)

            result["success"] = True
            result["rows_inserted"] = rows_to_insert

        except Exception as e:
            result["error"] = str(e)

        return result

    def generate_all(
        self,
        mode: str = "upsert",
        batch_size: int = 500,
        max_tables: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> GenerationStats:
        """
        为所有物理表生成虚拟数据。

        Args:
            mode: "upsert" | "overwrite"
            batch_size: 批量插入大小
            max_tables: 最大处理表数（None=全部）
            progress_callback: (table_name, index, total) -> None

        Returns:
            GenerationStats 生成统计
        """
        self.stats = GenerationStats()
        self.stats.start_time = datetime.now()

        tables = self.get_all_physical_tables()
        if max_tables:
            tables = tables[:max_tables]

        self.stats.total_tables = len(tables)

        for idx, table_name in enumerate(tables):
            # 进度回调
            if progress_callback:
                try:
                    progress_callback(table_name, idx + 1, len(tables))
                except Exception:
                    pass

            # 生成数据
            res = self.generate_for_table(table_name, mode=mode, batch_size=batch_size)

            if res["success"]:
                if res["rows_inserted"] > 0:
                    self.stats.tables_with_data += 1
                    self.stats.total_rows_generated += res["rows_inserted"]
                else:
                    self.stats.tables_skipped += 1
            else:
                self.stats.tables_failed += 1
                self.stats.errors.append(f"{table_name}: {res['error']}")

        self.stats.end_time = datetime.now()
        return self.stats

    def preview_table_data(
        self,
        table_name: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        预览表中已有数据（用于前端展示）。

        Returns:
            {"columns": [...], "rows": [[...], ...]}
        """
        try:
            columns = self.get_table_columns(table_name)
            with self.table_builder.engine.connect() as conn:
                query = text(f'SELECT * FROM "{table_name}" LIMIT :limit')
                result = conn.execute(query, {"limit": limit})

            rows = [list(row) for row in result.fetchall()]
            return {
                "columns": [c["name"] for c in columns],
                "rows": rows,
                "column_types": [c["type"] for c in columns],
                "total_rows": self.get_existing_row_count(table_name),
            }
        except Exception as e:
            return {"error": str(e), "columns": [], "rows": [], "column_types": []}


# ============================================================
# CLI 入口
# ============================================================

def run_cli():
    """命令行运行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="GenBFKit Mock Data Generator")
    parser.add_argument("--rows", "-r", type=int, default=100,
                        help="每个表生成的行数，默认 100")
    parser.add_argument("--seed", "-s", type=int, default=None,
                        help="随机数种子（用于可复现数据）")
    parser.add_argument("--mode", "-m", choices=["upsert", "overwrite"],
                        default="upsert", help="upsert=已有满100行跳过，overwrite=先清空再插入")
    parser.add_argument("--max", "-n", type=int, default=None,
                        help="最多处理表数（用于测试）")
    parser.add_argument("--batch", "-b", type=int, default=500,
                        help="批量插入大小")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="静默模式（不打印详细日志）")
    args = parser.parse_args()

    print("=" * 60)
    print("GenBFKit Mock Data Generator")
    print("=" * 60)

    generator = MockDataGenerator(rows_per_table=args.rows, seed=args.seed)

    def progress(name: str, idx: int, total: int):
        if not args.quiet:
            pct = idx / total * 100
            print(f"\r  [{idx}/{total}] ({pct:.1f}%) {name}...", end="", flush=True)

    print(f"\n开始生成数据（每表 {args.rows} 行）...")
    stats = generator.generate_all(
        mode=args.mode,
        batch_size=args.batch,
        max_tables=args.max,
        progress_callback=progress,
    )

    print("\n")
    print("=" * 60)
    print("生成完成!")
    print("=" * 60)
    print(f"  总表数:          {stats.total_tables}")
    print(f"  已生成数据:      {stats.tables_with_data} 张表")
    print(f"  跳过(已满):     {stats.tables_skipped} 张表")
    print(f"  失败:            {stats.tables_failed} 张表")
    print(f"  总生成行数:      {stats.total_rows_generated:,} 行")
    if stats.errors:
        print(f"\n  失败详情 (前5条):")
        for err in stats.errors[:5]:
            print(f"    - {err}")
    print("=" * 60)


if __name__ == "__main__":
    run_cli()
