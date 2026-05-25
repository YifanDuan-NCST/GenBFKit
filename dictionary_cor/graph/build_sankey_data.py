"""
从 prebuilt_full.json 全量数据生成桑葚图用 bf_sankey.csv

数据流向（完整层级）：
  Work type（工种） -> Data category（数据类别） -> Data pool（数据池） -> Dataset（数据集） -> Attribute（属性）

说明：
- Work type -> Category：工种下的数据类别数量
- Category -> Pool：类别下的数据池类型数量
- Pool -> Dataset：该数据池下的数据集数量
- Dataset -> Attribute：数据集所对应的属性字段数量（每个 dataset 继承其所属 pool 的属性模板）

value = 该路径下的数量（每个 dataset 计为 1，每个 attribute 计为 1）

用法：
  python build_sankey_data.py [prebuilt_full.json 路径]
  默认 JSON 路径为上一级目录的 prebuilt_full.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict

# 脚本所在目录 = graph/
SCRIPT_DIR = Path(__file__).resolve().parent
# 默认全量 JSON 路径：Construction_data_dictionary/prebuilt_full.json
DEFAULT_JSON_PATH = SCRIPT_DIR.parent / "prebuilt_full.json"
DEFAULT_CSV_PATH = SCRIPT_DIR / "bf_sankey.csv"


def load_prebuilt(json_path: Path) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_category_lookup(categories: list) -> dict:
    """(work_type_en, category_en) -> category_en（英文）"""
    # 直接返回 category_en，不再使用 category_zh
    return {
        (c["work_type_en"], c["category_en"]): c["category_en"]
        for c in categories
    }


def build_pool_lookup(pools: list) -> dict:
    """pool_en -> pool_en（英文）"""
    # 直接返回 pool_en，不再使用 pool_zh
    return {p["pool_en"]: p["pool_en"] for p in pools}


def build_sankey_links_full(data: dict, json_path: Path) -> list[tuple[str, str, float]]:
    """
    从全量 JSON 构建完整桑葚图链路（5层）：
    - Work type -> Category
    - Category -> Pool
    - Pool -> Dataset
    - Dataset -> Attribute

    返回：(source, target, value) 列表
    """
    categories = data.get("categories", [])
    pools = data.get("pools", [])
    datasets = data.get("datasets", [])
    attribute_templates = data.get("attribute_templates", {})

    cat_lookup = build_category_lookup(categories)
    pool_lookup = build_pool_lookup(pools)

    # 链路聚合
    link_wt_cat: dict[tuple[str, str], float] = defaultdict(float)
    link_cat_pool: dict[tuple[str, str], float] = defaultdict(float)
    link_pool_dataset: dict[tuple[str, str], float] = defaultdict(float)
    link_dataset_attr: dict[tuple[str, str], float] = defaultdict(float)

    for ds in datasets:
        wt = ds["work_type_en"]
        cat_en = ds["category_en"]
        pool_en = ds["pool_en"]
        dataset_en = ds["dataset_en"]

        category_zh = cat_lookup.get((wt, cat_en))
        if category_zh is None:
            category_zh = cat_en

        pool_zh = pool_lookup.get(pool_en)
        if pool_zh is None:
            pool_zh = pool_en

        # Work type -> Category
        link_wt_cat[(wt, category_zh)] += 1.0

        # Category -> Pool
        link_cat_pool[(category_zh, pool_zh)] += 1.0

        # Pool -> Dataset（使用 dataset_en 作为目标，显示英文名）
        link_pool_dataset[(pool_zh, dataset_en)] += 1.0

        # Dataset -> Attribute（该 dataset 所属 pool 的属性数量）
        attrs = attribute_templates.get(pool_en, {})
        attr_count = len(attrs) if attrs else 0
        # 每个 dataset 连接到其 pool 的每个属性（展示属性数量）
        if attr_count > 0:
            link_dataset_attr[(dataset_en, f"Attribute fields ({attr_count})")] += float(attr_count)

    rows = []
    for (src, tgt), val in link_wt_cat.items():
        rows.append((src, tgt, val))
    for (src, tgt), val in link_cat_pool.items():
        rows.append((src, tgt, val))
    for (src, tgt), val in link_pool_dataset.items():
        rows.append((src, tgt, val))
    for (src, tgt), val in link_dataset_attr.items():
        rows.append((src, tgt, val))

    return rows


def build_sankey_links_with_attributes(data: dict, json_path: Path) -> list[tuple[str, str, float]]:
    """
    从全量 JSON 构建完整桑葚图链路（5层）：
    - Work type -> Category
    - Category -> Pool
    - Pool -> Dataset
    - Dataset -> 具体 Attribute 名称

    这种方式会显示每个 dataset 对应的具体属性字段名。
    """
    categories = data.get("categories", [])
    pools = data.get("pools", [])
    datasets = data.get("datasets", [])
    attribute_templates = data.get("attribute_templates", {})

    cat_lookup = build_category_lookup(categories)
    pool_lookup = build_pool_lookup(pools)

    # 链路聚合
    link_wt_cat: dict[tuple[str, str], float] = defaultdict(float)
    link_cat_pool: dict[tuple[str, str], float] = defaultdict(float)
    link_pool_dataset: dict[tuple[str, str], float] = defaultdict(float)
    link_dataset_attr: dict[tuple[str, str], float] = defaultdict(float)

    for ds in datasets:
        wt = ds["work_type_en"]
        cat_en = ds["category_en"]
        pool_en = ds["pool_en"]
        dataset_en = ds["dataset_en"]

        category_zh = cat_lookup.get((wt, cat_en), cat_en)

        pool_zh = pool_lookup.get(pool_en, pool_en)

        # Work type -> Category
        link_wt_cat[(wt, category_zh)] += 1.0

        # Category -> Pool
        link_cat_pool[(category_zh, pool_zh)] += 1.0

        # Pool -> Dataset（使用 dataset_en 作为目标，显示英文名）
        link_pool_dataset[(pool_zh, dataset_en)] += 1.0

        # Dataset -> 具体 Attribute（显示属性字段名）
        attrs = attribute_templates.get(pool_en, {})
        if attrs:
            for attr_field_name in attrs.values():
                # 跳过空属性名
                if not attr_field_name:
                    continue
                link_dataset_attr[(dataset_en, attr_field_name)] += 1.0

    rows = []
    for (src, tgt), val in link_wt_cat.items():
        rows.append((src, tgt, val))
    for (src, tgt), val in link_cat_pool.items():
        rows.append((src, tgt, val))
    for (src, tgt), val in link_pool_dataset.items():
        rows.append((src, tgt, val))
    for (src, tgt), val in link_dataset_attr.items():
        rows.append((src, tgt, val))

    return rows


def write_csv(rows: list[tuple[str, str, float]], csv_path: Path) -> None:
    import csv
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "target", "value"])
        for src, tgt, val in rows:
            w.writerow([src, tgt, int(val) if val == int(val) else val])


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="从 prebuilt_full.json 生成桑葚图数据")
    parser.add_argument(
        "--full",
        action="store_true",
        help="生成完整5层链路（包含Dataset→Attribute），数据量约2.8万条"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="生成简化4层链路（到Dataset截止），数据量约2251条（推荐展示用）"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出 CSV 路径（默认 bf_sankey.csv）"
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        default=str(DEFAULT_JSON_PATH),
        help="prebuilt_full.json 路径"
    )
    args = parser.parse_args()

    json_path = Path(args.json_path)
    csv_path = Path(args.output) if args.output else DEFAULT_CSV_PATH

    if not json_path.exists():
        print(f"错误：未找到 {json_path}")
        sys.exit(1)

    print(f"读取全量数据: {json_path}")
    data = load_prebuilt(json_path)

    # 统计各层级数量
    print(f"数据统计:")
    print(f"  - Work types: {len(data.get('base_work_types', []))} 个")
    print(f"  - Categories: {len(data.get('categories', []))} 个")
    print(f"  - Pools: {len(data.get('pools', []))} 个")
    print(f"  - Datasets: {len(data.get('datasets', []))} 个")

    attr_templates = data.get("attribute_templates", {})
    total_attrs = sum(len(attrs) for attrs in attr_templates.values())
    print(f"  - Attribute fields: {total_attrs} 个（跨所有 pool）")

    # 判断使用哪种模式
    use_full = args.full or (not args.simple)

    if use_full:
        print("\n构建完整桑葚图链路（5层：Work type -> Category -> Pool -> Dataset -> Attribute）...")
        print("[!] 数据量约 2.8 万条，渲染可能较慢，建议用于数据分析而非展示")
        rows = build_sankey_links_with_attributes(data, json_path)
    else:
        print("\n构建简化桑葚图链路（4层：Work type -> Category -> Pool -> Dataset）...")
        print("[OK] 数据量约 2251 条，推荐用于展示")
        rows = build_sankey_links_full(data, json_path)

    write_csv(rows, csv_path)
    print(f"\n已写入 {len(rows)} 条链路 -> {csv_path}")

    # 统计各层链路数量
    work_types = {wt["work_type_en"] for wt in data.get("base_work_types", [])}
    wt_links = sum(1 for r in rows if r[0] in work_types)

    # Category -> Pool
    pool_zh_values = {p.get("pool_zh") or p["pool_en"] for p in data.get("pools", [])}
    cat_pool_links = sum(1 for r in rows if r[0] not in work_types and r[1] in pool_zh_values)

    # Pool -> Dataset
    dataset_values = {ds["dataset_en"] for ds in data.get("datasets", [])}
    pool_dataset_links = sum(1 for r in rows if r[0] in pool_zh_values and r[1] in dataset_values)

    # Dataset -> Attribute（剩下的都是这个）
    dataset_attr_links = len(rows) - wt_links - cat_pool_links - pool_dataset_links

    print(f"  - Work type -> Category: {wt_links} 条")
    print(f"  - Category -> Pool: {cat_pool_links} 条")
    print(f"  - Pool -> Dataset: {pool_dataset_links} 条")
    if use_full:
        print(f"  - Dataset -> Attribute: {dataset_attr_links} 条")


if __name__ == "__main__":
    main()
