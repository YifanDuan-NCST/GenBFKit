"""
数据字典核心数据模型

实现 GenBFKit 的 5 层链式数据字典结构:
  Work Type (8) → Data Category (98) → Data Pool (9) → Dataset/Params (2128) → Data Attribute (49)

该模块为独立可用的轻量级数据字典表示，不依赖外部数据源。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ──────────────────────────────────────────────
# 预定义的 9 种 Data Pool 类型
# ──────────────────────────────────────────────
@dataclass(frozen=True)
class DataPoolType:
    """数据池类型定义。"""
    name_en: str
    name_zh: str


# 标准 9 种数据池
STANDARD_DATA_POOLS: List[DataPoolType] = [
    DataPoolType("Continuous time-series data", "连续时序数据"),
    DataPoolType("Discrete time-series data", "离散时序数据"),
    DataPoolType("Text data", "文本数据"),
    DataPoolType("Binary status data", "二值状态数据"),
    DataPoolType("Controllable data", "可控数据"),
    DataPoolType("Constraint data", "约束数据"),
    DataPoolType("Batch time-series data", "批量时序数据"),
    DataPoolType("Image data", "图像数据"),
    DataPoolType("Response data", "响应数据"),
]

# 数据池对应的基础属性模板
POOL_BASE_ATTRIBUTES: Dict[str, List[str]] = {
    "Continuous time-series data": [
        "Timestamp", "Value", "Unit", "Quality_flag", "Sampling_frequency"
    ],
    "Discrete time-series data": [
        "Timestamp", "Value", "Unit", "Quality_flag", "Status_code"
    ],
    "Text data": [
        "Record_id", "Content", "Operator", "Record_time", "Source"
    ],
    "Binary status data": [
        "Timestamp", "Status", "Device_id", "Description"
    ],
    "Controllable data": [
        "Timestamp", "Set_value", "Actual_value", "Control_mode", "Unit"
    ],
    "Constraint data": [
        "Parameter", "Lower_limit", "Upper_limit", "Unit", "Constraint_type"
    ],
    "Batch time-series data": [
        "Batch_id", "Timestamp", "Value", "Unit", "Phase"
    ],
    "Image data": [
        "Image_id", "Capture_time", "Device_id", "Format", "Resolution", "Storage_path"
    ],
    "Response data": [
        "Timestamp", "Input_param", "Output_value", "Response_time", "Unit"
    ],
}

# 数据池特有的属性（在基础属性之上）
POOL_UNIQUE_ATTRIBUTES: Dict[str, List[str]] = {
    "Continuous time-series data": ["Sensor_id", "Calibration_date", "Drift_status"],
    "Discrete time-series data": ["Event_type", "Duration", "Trigger_source"],
    "Text data": ["Category", "Importance_level", "Attachment"],
    "Binary status data": ["Alert_threshold", "Ack_status", "Auto_reset"],
    "Controllable data": ["Ramp_rate", "Deadband", "PID_params"],
    "Constraint data": ["Violation_count", "Last_violation_time", "Severity"],
    "Batch time-series data": ["Product_spec", "Equipment_id", "Operator"],
    "Image data": ["Annotation", "ROI_coords", "Capture_condition"],
    "Response data": ["Model_id", "Confidence", "Prediction_horizon"],
}

# 预构建数据架构的简版摘要
PREBUILT_SUMMARY = {
    "work_type_count": 8,
    "category_count": 98,
    "pool_count": 9,
    "dataset_count": 2128,
    "attribute_count": 49,
    "work_types": [
        "Slag treating", "Hot blast supplying", "Gas & Dust treating",
        "Equipment maintaining", "Cooling monitoring", "Burden feeding",
        "BF tapping", "BF operating",
    ],
}


# ──────────────────────────────────────────────
# 数据字典层级实体
# ──────────────────────────────────────────────

@dataclass
class WorkType:
    """第1层：工种 (Work Type)"""
    name_en: str
    name_zh: str = ""
    no: int = 0


@dataclass
class DataCategory:
    """第2层：数据类别 (Data Category)"""
    work_type_en: str
    category_en: str
    category_zh: str = ""


@dataclass
class DataPool:
    """第3层：数据池 (Data Pool)"""
    pool_en: str
    pool_zh: str = ""


@dataclass
class Dataset:
    """第4层：数据集/参数 (Dataset/Parameter)"""
    work_type_en: str
    category_en: str
    pool_en: str
    dataset_en: str
    dataset_zh: str = ""
    dataset_zh_short: str = ""
    table_name: str = ""


@dataclass
class DataAttribute:
    """第5层：数据属性 (Data Attribute)"""
    pool_en: str
    attribute_name: str
    attribute_id: str = ""
    data_type: str = "float"
    description: str = ""


# ──────────────────────────────────────────────
# 链式查询结果
# ──────────────────────────────────────────────

@dataclass
class ChainQueryResult:
    """链式检索的结果。"""
    work_type: Optional[WorkType] = None
    categories: List[DataCategory] = field(default_factory=list)
    pools: List[DataPool] = field(default_factory=list)
    datasets: List[Dataset] = field(default_factory=list)
    attributes: List[DataAttribute] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_type": {
                "name_en": self.work_type.name_en if self.work_type else "",
                "name_zh": self.work_type.name_zh if self.work_type else "",
            } if self.work_type else None,
            "categories_count": len(self.categories),
            "pools_count": len(self.pools),
            "datasets_count": len(self.datasets),
            "attributes_count": len(self.attributes),
        }


# ──────────────────────────────────────────────
# 数据字典主类
# ──────────────────────────────────────────────

class DataDictionary:
    """
    GenBFKit 数据字典的独立表示。

    支持：
    - 从 prebuilt_full.json 加载
    - 链式检索 (Work Type → Category → Pool → Dataset → Attribute)
    - CRUD 操作
    - 完整的 5 层层级结构
    """

    def __init__(self):
        self.work_types: Dict[str, WorkType] = {}
        self.categories: Dict[str, List[DataCategory]] = {}
        self.pools: Dict[str, DataPool] = {}
        self.datasets: List[Dataset] = []
        self.attributes: Dict[str, List[DataAttribute]] = {}

    # ────── 加载 ──────

    @classmethod
    def load_from_json(cls, json_path: str | Path) -> "DataDictionary":
        """
        从 prebuilt_full.json 格式的文件加载数据字典。
        """
        d = cls()
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Data dictionary file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Work Types
        for wt in data.get("base_work_types", []):
            d.work_types[wt["work_type_en"]] = WorkType(
                name_en=wt["work_type_en"],
                name_zh=wt.get("work_type_zh", ""),
                no=wt.get("no", 0),
            )

        # 2. Categories
        for cat in data.get("categories", []):
            wt_en = cat["work_type_en"]
            if wt_en not in d.categories:
                d.categories[wt_en] = []
            d.categories[wt_en].append(DataCategory(
                work_type_en=wt_en,
                category_en=cat["category_en"],
                category_zh=cat.get("category_zh", ""),
            ))

        # 3. Pools
        for pool in data.get("pools", []):
            en = pool["pool_en"]
            d.pools[en] = DataPool(pool_en=en, pool_zh=pool.get("pool_zh", ""))

        # 4. Datasets
        for ds in data.get("datasets", []):
            d.datasets.append(Dataset(
                work_type_en=ds["work_type_en"],
                category_en=ds["category_en"],
                pool_en=ds["pool_en"],
                dataset_en=ds["dataset_en"],
                dataset_zh=ds.get("dataset_zh", ""),
                dataset_zh_short=ds.get("dataset_zh_short", ""),
                table_name=ds.get("table_name", ""),
            ))

        # 5. Attributes
        for pool_en, attrs in data.get("attribute_templates", {}).items():
            d.attributes[pool_en] = [
                DataAttribute(
                    pool_en=pool_en,
                    attribute_name=attr_name,
                    attribute_id=attr_id,
                )
                for attr_id, attr_name in attrs.items()
            ]

        return d

    @classmethod
    def create_prebuilt(cls) -> "DataDictionary":
        """
        创建基于预构建摘要的轻量数据字典（无需外部文件）。
        适用于测试和无文件环境。
        """
        d = cls()
        for wt_en in PREBUILT_SUMMARY["work_types"]:
            d.work_types[wt_en] = WorkType(name_en=wt_en, no=PREBUILT_SUMMARY["work_types"].index(wt_en) + 1)

        for pool_type in STANDARD_DATA_POOLS:
            d.pools[pool_type.name_en] = DataPool(pool_en=pool_type.name_en, pool_zh=pool_type.name_zh)

        # 预置基础属性模板
        for pool_en, base_attrs in POOL_BASE_ATTRIBUTES.items():
            unique_attrs = POOL_UNIQUE_ATTRIBUTES.get(pool_en, [])
            all_attrs = base_attrs + unique_attrs
            d.attributes[pool_en] = [
                DataAttribute(pool_en=pool_en, attribute_name=name, attribute_id=f"attr_{i}")
                for i, name in enumerate(all_attrs)
            ]

        return d

    # ────── 链式检索 ──────

    def chain_query(
        self,
        work_type: Optional[str] = None,
        category: Optional[str] = None,
        pool: Optional[str] = None,
        dataset: Optional[str] = None,
    ) -> ChainQueryResult:
        """
        链式检索：自上而下逐层过滤。

        Args:
            work_type: 工种名称（可选）
            category: 数据类别名称（可选，支持模糊匹配）
            pool: 数据池名称（可选）
            dataset: 数据集名称（可选，支持模糊匹配）

        Returns:
            匹配的链式结果
        """
        result = ChainQueryResult()

        # Step 1: Work Type
        if work_type:
            matched_wt = self.work_types.get(work_type)
            if matched_wt:
                result.work_type = matched_wt
                wt_list = [work_type]
            else:
                # 模糊匹配
                wt_list = [k for k in self.work_types if work_type.lower() in k.lower()]
                if wt_list:
                    result.work_type = self.work_types[wt_list[0]]
        else:
            wt_list = list(self.work_types.keys())

        # Step 2: Categories
        for wt_en in wt_list:
            cats = self.categories.get(wt_en, [])
            if category:
                cats = [c for c in cats if category.lower() in c.category_en.lower()]
            result.categories.extend(cats)

        # Step 3: Pools from matched categories
        matched_cat_keys = [(c.work_type_en, c.category_en) for c in result.categories]
        matched_pool_names = set()
        for ds in self.datasets:
            if (ds.work_type_en, ds.category_en) in matched_cat_keys:
                matched_pool_names.add(ds.pool_en)

        if pool:
            matched_pool_names = {p for p in matched_pool_names if pool.lower() in p.lower()}

        for pn in matched_pool_names:
            if pn in self.pools:
                result.pools.append(self.pools[pn])

        # Step 4: Datasets
        for ds in self.datasets:
            if (ds.work_type_en, ds.category_en) in matched_cat_keys:
                if ds.pool_en in matched_pool_names:
                    if dataset is None or dataset.lower() in ds.dataset_en.lower():
                        result.datasets.append(ds)

        # Step 5: Attributes
        for pn in matched_pool_names:
            result.attributes.extend(self.attributes.get(pn, []))

        return result

    def get_datasets_by_pool(self, pool_en: str) -> List[Dataset]:
        """按数据池获取所有数据集。"""
        return [ds for ds in self.datasets if ds.pool_en == pool_en]

    def get_attributes_for_pool(self, pool_en: str) -> List[DataAttribute]:
        """获取指定数据池的属性列表。"""
        return self.attributes.get(pool_en, [])

    def search_datasets(self, keyword: str) -> List[Dataset]:
        """关键词搜索数据集（匹配英文/中文名称）。"""
        kw = keyword.lower()
        results = []
        for ds in self.datasets:
            if kw in ds.dataset_en.lower() or kw in ds.dataset_zh.lower():
                results.append(ds)
        return results

    # ────── 统计 ──────

    def summary(self) -> Dict[str, Any]:
        """获取数据字典摘要统计。"""
        return {
            "work_types": len(self.work_types),
            "categories": sum(len(v) for v in self.categories.values()),
            "pools": len(self.pools),
            "datasets": len(self.datasets),
            "attributes": sum(len(v) for v in self.attributes.values()),
        }

    # ────── CRUD 支持 ──────

    def add_work_type(self, wt: WorkType) -> None:
        if wt.name_en not in self.work_types:
            self.work_types[wt.name_en] = wt

    def remove_work_type(self, name_en: str) -> bool:
        if name_en in self.work_types:
            del self.work_types[name_en]
            # 同时移除关联的 categories 和 datasets
            self.categories.pop(name_en, None)
            self.datasets = [ds for ds in self.datasets if ds.work_type_en != name_en]
            return True
        return False

    def add_dataset(self, ds: Dataset) -> None:
        self.datasets.append(ds)

    def remove_dataset(self, dataset_en: str, work_type_en: str = "") -> bool:
        original_len = len(self.datasets)
        if work_type_en:
            self.datasets = [
                ds for ds in self.datasets
                if not (ds.dataset_en == dataset_en and ds.work_type_en == work_type_en)
            ]
        else:
            self.datasets = [ds for ds in self.datasets if ds.dataset_en != dataset_en]
        return len(self.datasets) < original_len

    def add_attribute(self, attr: DataAttribute) -> None:
        if attr.pool_en not in self.attributes:
            self.attributes[attr.pool_en] = []
        self.attributes[attr.pool_en].append(attr)