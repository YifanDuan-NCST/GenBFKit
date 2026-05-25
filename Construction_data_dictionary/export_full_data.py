from __future__ import annotations

"""
全量数据导出脚本

用于将当前内存中的所有字典数据导出为完整的 JSON 文件。
导出格式与 prebuilt_full.json 一致，包含以下字段：
- base_work_types: 工种列表
- categories: 数据类别列表
- pools: 数据池类型列表
- datasets: 数据集列表
- attribute_templates: 属性模板字典

用法:
    python export_full_data.py [output_path]

示例:
    python export_full_data.py                    # 导出到默认路径 prebuilt_full.json
    python export_full_data.py my_export.json     # 导出到自定义路径
"""

import json
from pathlib import Path
import sys
import pandas as pd

_pkg_dir = Path(__file__).resolve().parent
_project_root = _pkg_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from Construction_data_dictionary import DictionaryManager


def _read_dataset_excel(path: Path) -> pd.DataFrame:
    """读取数据集 Excel 文件"""
    df = pd.read_excel(path, sheet_name=0)
    # 规范化列名
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _read_attribute_excel(path: Path) -> pd.DataFrame:
    """读取属性模板 Excel 文件"""
    df = pd.read_excel(path, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _work_type_to_zh(work_type_en: str) -> str:
    """工种英文名到中文名的映射"""
    mapping = {
        "Slag treating": "渣处理",
        "Hot blast supplying": "热风供给",
        "Gas & Dust treating": "煤气处理",
        "Equipment maintaining": "设备维护",
        "Cooling monitoring": "冷却监测",
        "Burden feeding": "布料监控",
        "BF tapping": "出铁作业",
        "BF operating": "高炉操作",
    }
    return mapping.get(work_type_en, "")


def _pool_en_to_zh(pool_en: str) -> str:
    """数据池英文名到中文名的映射"""
    mapping = {
        "Continuous time-series data": "连续时序数据",
        "Discrete time-series data": "离散时序数据",
        "Text data": "文本数据",
        "Binary status data": "二值状态数据",
        "Controllable data": "可控数据",
        "Constraint data": "约束数据",
        "Batch time-series data": "批量时序数据",
        "Image data": "图像数据",
        "Response data": "响应数据",
    }
    return mapping.get(pool_en, "")


def export_full_data(output_path: str | Path | None = None) -> dict:
    """
    导出全量数据字典为 JSON 格式。

    数据读取顺序：
    1. 优先从 Excel 文件读取（dataset_dictionary.xlsx, data_attribute_dictionary.xlsx）
    2. 若无 Excel 文件，则从预构建数据 prebuilt_default.py 读取

    Args:
        output_path: 输出文件路径。默认为 None，表示导出到当前目录的 prebuilt_full.json

    Returns:
        包含全量数据的字典
    """
    # 检查 Excel 文件是否存在（从项目根目录查找）
    # Excel 文件位于 Construction_data_dictionary 的父目录
    dataset_excel_path = _project_root / "dataset_dictionary.xlsx"
    attr_excel_path = _project_root / "data_attribute_dictionary.xlsx"

    has_excel = dataset_excel_path.exists() and attr_excel_path.exists()

    # 构建导出数据结构
    export_data: dict = {
        "base_work_types": [],
        "categories": [],
        "pools": [],
        "datasets": [],
        "attribute_templates": {},
    }

    if has_excel:
        # 方式1: 从 Excel 文件读取数据
        print("检测到 Excel 文件，从 Excel 读取数据...")
        df = _read_dataset_excel(dataset_excel_path)
        attr_df = _read_attribute_excel(attr_excel_path)

        print(f"读取到 {len(df)} 条数据集记录")
        print(f"读取到 {len(attr_df)} 行属性定义")

        # 1. 提取并导出 base_work_types (从数据集 Excel 中提取唯一的工种)
        unique_work_types = df['Work type'].dropna().unique() if 'Work type' in df.columns else []
        if not unique_work_types:
            # 尝试其他列名
            for col in df.columns:
                if 'work' in col.lower() and 'type' in col.lower():
                    unique_work_types = df[col].dropna().unique()
                    break

        for i, wt in enumerate(unique_work_types, 1):
            export_data["base_work_types"].append({
                "work_type_en": wt,
                "work_type_zh": _work_type_to_zh(wt),
                "no": i,
            })

        # 2. 提取并导出 categories
        # 假设 Excel 中有 work_type, category_en, category_zh_cn 等列
        category_cols = [c for c in df.columns if 'category' in c.lower()]
        if category_cols:
            # 去重
            seen = set()
            for _, row in df.iterrows():
                for cat_col in category_cols:
                    if pd.notna(row.get(cat_col)):
                        key = (row.get('Work type', ''), row.get(cat_col))
                        if key not in seen:
                            seen.add(key)
                            zh = row.get('category_zh_cn', '') if 'category_zh_cn' in df.columns else ''
                            export_data["categories"].append({
                                "work_type_en": str(row.get('Work type', '')),
                                "category_en": str(row.get(cat_col)),
                                "category_zh": str(zh) if pd.notna(zh) else "",
                            })

        # 3. 提取并导出 pools (全局 9 类 pool types)
        pool_cols = [c for c in df.columns if 'pool' in c.lower() and 'en' in c.lower()]
        if pool_cols:
            seen_pools = set()
            for pool_col in pool_cols:
                for pool_en in df[pool_col].dropna().unique():
                    if pool_en not in seen_pools:
                        seen_pools.add(pool_en)
                        export_data["pools"].append({
                            "pool_en": pool_en,
                            "pool_zh": _pool_en_to_zh(pool_en),
                        })

        # 4. 导出 datasets (所有数据集记录)
        dataset_en_col = next((c for c in df.columns if c.lower() == 'dataset'), None)
        if dataset_en_col:
            for _, row in df.iterrows():
                dataset_en = row.get(dataset_en_col, '')
                if pd.notna(dataset_en):
                    zh = row.get('dataset_zh_cn', '') if 'dataset_zh_cn' in df.columns else ''
                    export_data["datasets"].append({
                        "work_type_en": str(row.get('Work type', '')),
                        "category_en": str(row.get(category_cols[0], '')) if category_cols else '',
                        "pool_en": str(row.get(pool_cols[0], '')) if pool_cols else '',
                        "dataset_en": str(dataset_en),
                        "dataset_zh": str(zh) if pd.notna(zh) else "",
                        "dataset_zh_short": str(zh) if pd.notna(zh) else "",
                    })

        # 5. 导出 attribute_templates
        if len(attr_df.columns) > 1:
            pool_columns = attr_df.columns[1:]  # 第一列是 attribute_id
            for pool_col in pool_columns:
                attrs = {}
                for row_idx in range(len(attr_df)):
                    attr_id = str(attr_df.iloc[row_idx, 0])
                    attr_name = attr_df.iloc[row_idx][pool_col]
                    if pd.notna(attr_name):
                        attrs[attr_id] = str(attr_name)
                if attrs:
                    export_data["attribute_templates"][str(pool_col)] = attrs

    else:
        # 方式2: 从预构建数据 prebuilt_default.py 读取
        print("未检测到 Excel 文件，从预构建数据 prebuilt_default.py 读取...")

        # 创建 DictionaryManager 并加载预构建数据
        mgr = DictionaryManager()
        mgr.load_prebuilt_default(overwrite=True)

        # 1. 获取 base_work_types
        for item in mgr.base_dict.list_all():
            export_data["base_work_types"].append({
                "work_type_en": item.work_type_en,
                "work_type_zh": item.work_type_zh or "",
                "no": item.no or 0,
            })

        # 2. 获取 categories
        for item in mgr.category_dict.list_all():
            export_data["categories"].append({
                "work_type_en": item.work_type_en,
                "category_en": item.category_en,
                "category_zh": item.category_zh or "",
            })

        # 3. 获取 pools (去重)
        seen_pool_en = set()
        for item in mgr.pool_dict.list_all():
            if item.pool_en and item.pool_en not in seen_pool_en:
                seen_pool_en.add(item.pool_en)
                export_data["pools"].append({
                    "pool_en": item.pool_en,
                    "pool_zh": item.pool_zh or "",
                })

        # 4. 获取 datasets
        for item in mgr.dataset_dict.list_all():
            export_data["datasets"].append({
                "work_type_en": item.work_type_en,
                "category_en": item.category_en,
                "pool_en": item.pool_en,
                "dataset_en": item.dataset_en,
                "dataset_zh": item.dataset_zh or "",
                "dataset_zh_short": item.dataset_zh_short or "",
            })

        # 5. 获取 attribute_templates
        for pool_type in mgr.attr_dict.list_pool_types():
            export_data["attribute_templates"][pool_type] = mgr.attr_dict.get_attributes_for_pool_type(pool_type)

    # 打印统计信息
    print()
    print("导出数据统计:")
    print(f"  - base_work_types: {len(export_data['base_work_types'])} 条")
    print(f"  - categories: {len(export_data['categories'])} 条")
    print(f"  - pools: {len(export_data['pools'])} 条")
    print(f"  - datasets: {len(export_data['datasets'])} 条")
    print(f"  - attribute_templates: {len(export_data['attribute_templates'])} 个 pool_type")

    # 打印 attribute_templates 的详情
    print()
    print("Attribute templates 详情:")
    for pool_en, attrs in export_data["attribute_templates"].items():
        print(f"  - {pool_en}: {len(attrs)} 个属性")

    # 保存到文件
    if output_path is None:
        output_path = _pkg_dir / "prebuilt_full.json"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print()
    print(f"全量数据已导出到: {output_path}")

    return export_data


def main() -> None:
    """主函数，支持命令行参数。"""
    # 解析命令行参数
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = None

    export_full_data(output_path)


if __name__ == "__main__":
    main()
