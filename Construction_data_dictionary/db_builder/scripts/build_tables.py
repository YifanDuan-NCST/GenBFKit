# -*- coding: utf-8 -*-
"""从 JSON 构建所有数据库表脚本"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
# 脚本路径: db_builder/scripts/build_tables.py
# 向上三级到达 Construction_data_dictionary/
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from db_builder.services.database_manager import DatabaseManager
from db_builder.config import DatabaseSettings


def main():
    parser = argparse.ArgumentParser(
        description="GenBFKit 数据库表构建工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 一体化构建（推荐）：自动完成初始化 + 增量导入 + 自适应建表
  python db_builder/scripts/build_tables.py --full --json prebuilt_full.json

  # 增量导入（先初始化后增量）
  python db_builder/scripts/build_tables.py --incremental --json prebuilt_full.json

  # 全量重建：覆盖所有物理表（慎用，会丢失数据）
  python db_builder/scripts/build_tables.py --json prebuilt_full.json --overwrite

  # 仅回填中文列（不重建表）
  python db_builder/scripts/build_tables.py --backfill
"""
    )
    parser.add_argument("--json", "-j", type=str, default=None,
                        help="JSON 数据文件路径（默认: prebuilt_full.json）")
    parser.add_argument("--host", type=str, default="localhost",
                        help="数据库主机（默认: localhost）")
    parser.add_argument("--port", "-p", type=int, default=5432,
                        help="数据库端口（默认: 5432）")
    parser.add_argument("--database", "-d", type=str, default="genbfkit",
                        help="数据库名称（默认: genbfkit）")
    parser.add_argument("--username", "-u", type=str, default="postgres",
                        help="数据库用户名（默认: postgres）")
    parser.add_argument("--password", "-w", type=str, default=None,
                        help="数据库密码（可从环境变量 GENBFKIT__DATABASE__PASSWORD 读取）")
    parser.add_argument("--overwrite", "-o", action="store_true",
                        help="覆盖已存在的物理表（仅与 --incremental 配合使用）")
    parser.add_argument("--backfill", "-b", action="store_true",
                        help="仅回填 meta_datasets 中缺失的中文列（不重建表）")
    parser.add_argument("--incremental", "-i", action="store_true",
                        help="增量导入模式：自动检测新增数据集和属性变更，一体化完成")
    parser.add_argument("--full", "-f", action="store_true",
                        help="一体化构建：初始化元数据表 + 增量导入 + 自适应建表（等同于 init + --incremental 的合集）")

    args = parser.parse_args()

    # 获取密码：命令行参数 > 环境变量 > 交互式输入
    password = args.password or os.environ.get("GENBFKIT__DATABASE__PASSWORD", "")

    if not password:
        password = input("请输入数据库密码: ").strip()

    # JSON 数据文件路径：相对路径统一基于 project_root 解析
    if args.json:
        json_path_input = Path(args.json)
        if json_path_input.is_absolute():
            json_path = json_path_input
        else:
            json_path = project_root / json_path_input
    else:
        json_path = project_root / "prebuilt_full.json"

    print("=" * 60)
    print("GenBFKit 数据库表构建工具")
    print("=" * 60)
    print(f"\n数据库配置:")
    print(f"  主机: {args.host}:{args.port}")
    print(f"  数据库: {args.database}")
    print(f"  用户: {args.username}")
    print(f"\nJSON 数据文件: {json_path}")

    if not json_path.exists():
        print(f"\n错误: JSON 文件不存在: {json_path}")
        print("请使用 --json 参数指定正确的路径")
        return

    # 配置数据库连接
    db_settings = DatabaseSettings(
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=password,
    )

    # 初始化管理器
    manager = DatabaseManager(db_settings=db_settings, json_path=json_path)

    # 健康检查
    print("\n[*] 检查数据库连接...")
    health = manager.health_check()
    print(f"  状态: {health.status}")

    if not health.database_connected:
        print("\n错误: 无法连接到数据库!")
        print("提示: 确保 PostgreSQL 服务正在运行，且用户名/密码正确")
        return

    if not health.metadata_tables_exist:
        print("\n警告: 元数据表不存在，尝试初始化...")
        result = manager.initialize_database()
        if not result["success"]:
            print(f"错误: 初始化失败: {result['message']}")
            return
        print("  [OK] 元数据表已初始化")

    # ── 一体化构建模式（自动完成：初始化 + 增量导入 + 自适应建表） ──
    if args.full:
        print("\n[*] 一体化构建模式")
        print("  自动完成：初始化元数据表 → 增量导入 → 自适应建表")

        # Step 1: 初始化元数据表
        if not health.metadata_tables_exist:
            print("\n  [Step 1/3] 初始化元数据表...")
            init_result = manager.initialize_database()
            if not init_result["success"]:
                print(f"  错误: 初始化失败: {init_result['message']}")
                return
            print("  [OK] 元数据表已初始化")
        else:
            print("\n  [Step 1/3] 元数据表已存在，跳过初始化")

        # Step 2: 增量导入
        print("\n  [Step 2/3] 增量导入（自动检测新增数据 + 属性变更）...")
        result = manager.incremental_import(json_path)

        print("\n  === 导入结果 ===")
        imp = result.get("import_stats", {})
        print(f"  新增工种: {imp.get('work_types', 0)}")
        print(f"  新增类别: {imp.get('categories', 0)}")
        print(f"  新增数据池: {imp.get('pools', 0)}")
        print(f"  新增数据集: {imp.get('datasets', 0)}")
        print(f"  属性模板新增: {imp.get('attribute_templates_new', 0)}")
        print(f"  属性模板更新: {imp.get('attribute_templates_updated', 0)}")

        rebuild_types = result.get("rebuild_pool_types", [])
        if rebuild_types:
            print(f"\n  === 属性变更检测 ===")
            print(f"  以下池类型属性已变更:")
            for pt in rebuild_types:
                print(f"    - {pt}")
            rebuild = result.get("rebuild_response", {})
            print(f"\n  重建结果: {rebuild.get('tables_recreated', 0)} 张表重建，"
                  f"{rebuild.get('tables_failed', 0)} 张失败")

        new_tables = result.get("build_response", {})
        if new_tables:
            print(f"\n  === 新增数据集建表 ===")
            print(f"  新建表: {new_tables.get('tables_created', 0)} 张，"
                  f"跳过: {new_tables.get('tables_skipped', 0)} 张，"
                  f"失败: {new_tables.get('tables_failed', 0)} 张")

        print(f"\n  {result.get('message', '')}")

        stats = manager.get_statistics()
        print(f"\n  === 最终统计 ===")
        print(f"  工种: {stats.total_work_types}")
        print(f"  数据集: {stats.total_datasets}")
        print(f"  物理表: {stats.total_tables}")
        print("\n" + "=" * 60)
        print("一体化构建完成!")
        print("=" * 60)
        return
    # ─────────────────────────────────────────────────────────────────────

    # ── 增量导入模式 ──────────────────────────────────────────────
    if args.incremental:
        print("\n[*] 增量导入模式（自动检测新增数据集 + 属性变更）...")
        print("  这将一体化完成：元数据导入 → 新增表构建 → 属性变更表重建")
        result = manager.incremental_import(json_path)

        print("\n  === 导入结果 ===")
        imp = result.get("import_stats", {})
        print(f"  新增工种: {imp.get('work_types', 0)}")
        print(f"  新增类别: {imp.get('categories', 0)}")
        print(f"  新增数据池: {imp.get('pools', 0)}")
        print(f"  新增数据集: {imp.get('datasets', 0)}")
        print(f"  属性模板新增: {imp.get('attribute_templates_new', 0)}")
        print(f"  属性模板更新: {imp.get('attribute_templates_updated', 0)}")

        rebuild_types = result.get("rebuild_pool_types", [])
        if rebuild_types:
            print(f"\n  === 属性变更检测 ===")
            print(f"  以下池类型属性已变更，需重建其物理表:")
            for pt in rebuild_types:
                print(f"    - {pt}")
            rebuild = result.get("rebuild_response", {})
            print(f"\n  重建结果: {rebuild.get('tables_recreated', 0)} 张表重建，"
                  f"{rebuild.get('tables_failed', 0)} 张失败")
            if rebuild.get("errors"):
                for err in rebuild["errors"][:5]:
                    print(f"    错误: {err}")
        else:
            print("\n  无属性变更的池类型，跳过重建步骤")

        new_tables = result.get("build_response", {})
        if new_tables:
            print(f"\n  === 新增数据集建表 ===")
            print(f"  新建表: {new_tables.get('tables_created', 0)} 张，"
                  f"跳过: {new_tables.get('tables_skipped', 0)} 张，"
                  f"失败: {new_tables.get('tables_failed', 0)} 张")
            if new_tables.get("errors"):
                for err in new_tables["errors"][:5]:
                    print(f"    错误: {err}")
        else:
            pending = result.get("datasets_pending", 0)
            print(f"\n  无新增待建表数据集（pending={pending}）")

        print(f"\n  {result.get('message', '')}")

        stats = manager.get_statistics()
        print(f"\n  === 最终统计 ===")
        print(f"  工种: {stats.total_work_types}")
        print(f"  数据集: {stats.total_datasets}")
        print(f"  物理表: {stats.total_tables}")
        print("\n" + "=" * 60)
        print("增量导入完成!")
        print("=" * 60)
        return
    # ─────────────────────────────────────────────────────────────

    # 单独回填中文列（不重建表）
    if args.backfill:
        print("\n[*] 回填 meta_datasets 缺失的中文列...")
        stats = manager.backfill_chinese_columns()
        total = sum(stats.values())
        print(f"  回填完成: work_type_zh={stats['work_type_zh']}  "
              f"category_zh={stats['category_zh']}  pool_zh={stats['pool_zh']}  "
              f"总计={total}")
        return

    # 构建表（默认：跳过已存在的表）
    print("\n[*] 构建物理数据表（默认跳过已存在的表）...")
    print("  如需覆盖重建，请添加 --overwrite 参数")
    print("  推荐使用 --incremental 参数进行增量导入")

    response = manager.build_tables(json_path=json_path, overwrite=args.overwrite)

    print(f"\n  结果:")
    print(f"    创建: {response.tables_created} 张表")
    print(f"    跳过: {response.tables_skipped} 张表")
    print(f"    失败: {response.tables_failed} 张表")
    print(f"    耗时: {response.duration_seconds} 秒")

    if response.errors and len(response.errors) > 0:
        print(f"\n  错误详情:")
        for error in response.errors[:10]:
            print(f"    - {error}")
        if len(response.errors) > 10:
            print(f"    ... 还有 {len(response.errors) - 10} 个错误")

    # 统计
    stats = manager.get_statistics()

    print("\n" + "=" * 60)
    print("构建完成!")
    print("=" * 60)
    print(f"\n最终统计:")
    print(f"  工种: {stats.total_work_types}")
    print(f"  数据集: {stats.total_datasets}")
    print(f"  物理表: {response.tables_created}")
    print(f"  总记录: 0")


if __name__ == "__main__":
    main()
