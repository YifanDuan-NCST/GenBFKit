#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
demo_import_simple.py - 快速模板导入示例

本脚本展示如何使用 Data_Import_Template_Simple.xlsx（快速模板）进行数据快速导入。

快速模板说明：
- 仅需4列数据：Work Type, Data Category, Data Pool, Dataset
- 池类型必须是预定义的9种标准类型之一
- 系统会自动创建关联的工种和数据类别

预定义的9种标准池类型：
1. Continuous time-series data (连续时序数据)
2. Discrete time-series data (离散时序数据)
3. Batch time-series data (批量时序数据)
4. Text data (文本数据)
5. Image data (图像数据)
6. Binary status data (二值状态数据)
7. Controllable data (可控数据)
8. Constraint data (约束数据)
9. Response data (响应数据)

使用方法：
1. 在 Data_Import_Template_Simple.xlsx 中填入需要导入的数据
2. 运行本脚本：
   python demo_import_simple.py

与全量模板的区别：
- 全量模板 (Data_Import_Template.xlsx): 可以完整定义所有层级，包括自定义池类型和属性模板
- 快速模板 (Data_Import_Template_Simple.xlsx): 仅能导入数据集，池类型必须是预定义的9种标准类型

输出：
- 导入成功的数据条数统计
- 当前管理器的所有数据内容
"""

from pathlib import Path
import sys

# Allow running as a plain script: python Construction_data_dictionary/demo_import_simple.py
_pkg_dir = Path(__file__).resolve().parent
_project_root = _pkg_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from Construction_data_dictionary import DictionaryManager


def main():
    print("=" * 70)
    print("Demo: Simple Template Import (Quick Import)")
    print("=" * 70)

    # 快速模板文件路径
    simple_template_path = _pkg_dir / "templates" / "Data_Import_Template_Simple.xlsx"

    # 1. 创建管理器实例
    print("\n[Step 1] Create DictionaryManager instance...")
    mgr = DictionaryManager()

    # 2. 先加载预构建数据（基础数据）
    print("\n[Step 2] Load prebuilt default data...")
    count_prebuilt = mgr.load_prebuilt_default()
    print(f"   Prebuilt data loaded: {count_prebuilt} items")

    # 显示当前工种
    work_types = mgr.get_work_types()
    print(f"\n   Current work types ({len(work_types)}):")
    for wt in work_types[:5]:
        print(f"     - {wt}")
    if len(work_types) > 5:
        print(f"     ... and {len(work_types) - 5} more")

    # 3. 使用快速模板导入
    print("\n" + "=" * 70)
    print("[Step 3] Import data using simple template")
    print("=" * 70)

    if simple_template_path.exists():
        print(f"\n[OK] Found simple template file: {simple_template_path}")
        print("\n[INFO] Simple template format:")
        print("   Column 1: Work Type (工种英文标识)")
        print("   Column 2: Data Category (数据类别英文标识)")
        print("   Column 3: Data Pool (必须是预定义的9种标准类型之一)")
        print("   Column 4: Dataset (数据集英文标识)")

        print("\n[INFO] Supported Data Pool types (9 types):")
        print("   1. Continuous time-series data (连续时序数据)")
        print("   2. Discrete time-series data (离散时序数据)")
        print("   3. Batch time-series data (批量时序数据)")
        print("   4. Text data (文本数据)")
        print("   5. Image data (图像数据)")
        print("   6. Binary status data (二值状态数据)")
        print("   7. Controllable data (可控数据)")
        print("   8. Constraint data (约束数据)")
        print("   9. Response data (响应数据)")

        print("\n[Processing] Importing data from simple template...")
        result = mgr.import_from_simple_template(
            simple_template_path,
            overwrite=False
        )

        print("\n[Result] Import summary:")
        print(f"   - Work types added:   {result['work_types_added']}")
        print(f"   - Categories added:  {result['categories_added']}")
        print(f"   - Datasets added:    {result['datasets_added']}")
        print(f"   - Rows skipped:      {result['rows_skipped']}")

        total_added = result['work_types_added'] + result['categories_added'] + result['datasets_added']
        if total_added > 0:
            print(f"\n[OK] {total_added} new records imported")
        else:
            print("\n[Info] No new records imported (data may already exist or template is empty)")
    else:
        print(f"\n[Error] Simple template file not found: {simple_template_path}")
        print("   Please ensure the template file exists in templates/ directory")

    # 4. 展示数据
    print("\n" + "=" * 70)
    print("[Step 4] View imported data")
    print("=" * 70)

    current_work_types = mgr.get_work_types()
    print(f"\nTotal work types: {len(current_work_types)}")

    if current_work_types:
        first_wt = current_work_types[0]
        print(f"\n[Chain] Full data hierarchy for work type '{first_wt}':")
        chain = mgr.get_full_data_chain(first_wt, include_attributes=True)

        for cat in chain["data_chain"]:
            print(f"\n   [Category] {cat['category_en']} ({cat['category_zh']})")
            for pool in cat["pools"]:
                print(f"      [Pool] {pool['pool_en']} ({pool['pool_zh']})")
                for ds in pool["datasets"][:3]:
                    print(f"         [Dataset] {ds['dataset_en']} - {ds['dataset_zh']}")
                if len(pool["datasets"]) > 3:
                    print(f"         ... and {len(pool['datasets']) - 3} more datasets")

    # 5. 导出数据
    print("\n" + "=" * 70)
    print("[Step 5] Export data to JSON")
    print("=" * 70)

    output_path = _pkg_dir / "imported_data_simple.json"
    mgr.export_to_json(output_path)
    print(f"\n[OK] Data exported to: {output_path}")

    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)
    print("\n[Template Usage Guide]:")
    print("   - Simple Template: Quick dataset import (4 columns only)")
    print("   - Full Template: Full control over all 5 levels")
    print("\n[Next Steps]:")
    print("   1. View imported_data_simple.json for complete exported data")
    print("   2. Modify templates/Data_Import_Template_Simple.xlsx to add more data")
    print("   3. See demo_import_full.py for full template import")


if __name__ == "__main__":
    main()
