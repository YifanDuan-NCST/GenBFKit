#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
demo_import_full.py - 全量字典格式导入示例

本脚本展示如何使用 Data_Import_Template.xlsx（全量模板）进行数据增量导入。

双模板机制说明：
1. Data_Import_Template.xlsx（全量模板）：
   - Sheet 1: Base Dict (work_type) - 添加新的工种
   - Sheet 2: Data Category (category_dict) - 添加新的数据类别
   - Sheet 3: Data Pool (Pool_dict) - 添加新的数据池
   - Sheet 4: Dataset Dict (Dataset_dict) - 添加新的数据集/参数
   - Sheet 5: Data Attribute (Attr_dict) - 添加数据属性模板
   特点：可以完整定义所有层级，包括自定义池类型和属性模板

2. Data_Import_Template_Simple.xlsx（快速模板）：
   - 快速导入数据集，仅需4列
   - 池类型必须是预定义的9种标准类型
   特点：简单快速，适合快速添加数据集

使用方法：
1. 在 Data_Import_Template.xlsx 中填入需要导入的数据
2. 运行本脚本：
   python demo_import_full.py

与快速模板的区别：
- 快速模板 (Data_Import_Template_Simple.xlsx): 仅能导入数据集，且池类型必须是预定义的9种标准类型
- 全量模板 (Data_Import_Template.xlsx): 可以完整定义所有层级，包括自定义池类型和属性模板

输出：
- 导入成功的数据条数统计
- 当前管理器的所有数据内容
"""

from pathlib import Path
import sys

# Allow running as a plain script: python Construction_data_dictionary/demo_import_full.py
_pkg_dir = Path(__file__).resolve().parent
_project_root = _pkg_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from Construction_data_dictionary import DictionaryManager


def main():
    print("=" * 70)
    print("Demo: Full Dictionary Format Import (Full Template)")
    print("=" * 70)

    # 全量模板文件路径
    full_template_path = _pkg_dir / "templates" / "Data_Import_Template.xlsx"
    # 快速模板文件路径（备用）
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
    for wt in work_types[:5]:  # 只显示前5个
        print(f"     - {wt}")
    if len(work_types) > 5:
        print(f"     ... and {len(work_types) - 5} more")

    # 3. 使用全量模板导入（Sheet 1-5）
    print("\n" + "=" * 70)
    print("[Step 3] Import data using full template")
    print("=" * 70)

    if full_template_path.exists():
        print(f"\n[OK] Found full template file: {full_template_path}")
        print("\n[INFO] Full template contains the following Sheets:")
        print("   Sheet 1: Base Dict (work_type)         - Work type dictionary")
        print("   Sheet 2: Data Category (category_dict) - Data category dictionary")
        print("   Sheet 3: Data Pool (Pool_dict)          - Data pool dictionary")
        print("   Sheet 4: Dataset Dict (Dataset_dict)    - Dataset dictionary")
        print("   Sheet 5: Data Attribute (Attr_dict)     - Attribute template dictionary")

        # 调用全量格式导入
        print("\n[Processing] Importing data from full template...")
        counts = mgr.import_additional_data(
            full_template_path,
            overwrite=False  # 不覆盖已存在的数据
        )

        print("\n[Result] Import summary:")
        print(f"   - Base Dictionary (work types):     {counts['base_dictionary']} items")
        print(f"   - Category Dictionary (categories): {counts['data_category_dictionary']} items")
        print(f"   - Pool Dictionary (data pools):    {counts['data_pool_dictionary']} items")
        print(f"   - Dataset Dictionary (datasets):   {counts['dataset_dictionary']} items")
        print(f"   - Attribute Dictionary (attrs):    {counts['data_attribute_dictionary']} items")

        total_imported = sum(counts.values())
        if total_imported > 0:
            print(f"\n[OK] {total_imported} new records imported")
        else:
            print("\n[Info] No new records imported (data may already exist or template is empty)")
    else:
        print(f"\n[Warning] Full template file not found: {full_template_path}")
        if simple_template_path.exists():
            print(f"   Falling back to simple template: {simple_template_path}")
            print("\n[Processing] Importing data from simple template...")
            result = mgr.import_from_simple_template(
                simple_template_path,
                overwrite=False
            )
            print(f"\n[Result] Import summary:")
            print(f"   - Work types added: {result['work_types_added']}")
            print(f"   - Categories added: {result['categories_added']}")
            print(f"   - Datasets added: {result['datasets_added']}")
            print(f"   - Rows skipped: {result['rows_skipped']}")
        else:
            print("\n[Error] No template files found!")

    # 4. 展示完整数据链
    print("\n" + "=" * 70)
    print("[Step 4] View imported data")
    print("=" * 70)

    current_work_types = mgr.get_work_types()
    print(f"\nTotal work types: {len(current_work_types)}")

    if current_work_types:
        # 展示第一个工种的完整数据链
        first_wt = current_work_types[0]
        print(f"\n[Chain] Full data hierarchy for work type '{first_wt}':")
        chain = mgr.get_full_data_chain(first_wt, include_attributes=True)

        for cat in chain["data_chain"]:
            print(f"\n   [Category] {cat['category_en']} ({cat['category_zh']})")
            for pool in cat["pools"]:
                print(f"      [Pool] {pool['pool_en']} ({pool['pool_zh']})")
                for ds in pool["datasets"][:3]:  # 每个池只显示前3个数据集
                    print(f"         [Dataset] {ds['dataset_en']} - {ds['dataset_zh']}")
                if len(pool["datasets"]) > 3:
                    print(f"         ... and {len(pool['datasets']) - 3} more datasets")

    # 5. 导出数据
    print("\n" + "=" * 70)
    print("[Step 5] Export data to JSON")
    print("=" * 70)

    output_path = _pkg_dir / "imported_data_full.json"
    mgr.export_to_json(output_path)
    print(f"\n[OK] Data exported to: {output_path}")

    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)
    print("\n[Template Usage Guide]:")
    print("   - Full Template (Data_Import_Template.xlsx): Full control over all 5 levels")
    print("   - Simple Template (Data_Import_Template_Simple.xlsx): Quick dataset import only")
    print("\n[Next Steps]:")
    print("   1. View imported_data_full.json for complete exported data")
    print("   2. Modify templates/Data_Import_Template.xlsx to add more data")
    print("   3. Run this script again for incremental import")


if __name__ == "__main__":
    main()
