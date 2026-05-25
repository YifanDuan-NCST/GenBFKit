# -*- coding: utf-8 -*-
"""示例脚本 - 演示如何使用数据库构建模块"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from db_builder.services.database_manager import DatabaseManager
from db_builder.config import DatabaseSettings


def main():
    parser = argparse.ArgumentParser(description="GenBFKit 数据库构建示例")
    parser.add_argument("--host", type=str, default="localhost", help="数据库主机")
    parser.add_argument("--port", "-p", type=int, default=5432, help="数据库端口")
    parser.add_argument("--database", "-d", type=str, default="genbfkit", help="数据库名称")
    parser.add_argument("--username", "-u", type=str, default="postgres", help="数据库用户名")
    parser.add_argument("--password", "-w", type=str, default=None, help="数据库密码")
    parser.add_argument("--json", "-j", type=str, default=None, help="JSON数据文件路径")

    args = parser.parse_args()

    # 获取密码：命令行参数 > 环境变量 > 交互式输入
    password = args.password or os.environ.get("GENBFKIT__DATABASE__PASSWORD", "")

    if not password:
        password = input("请输入数据库密码: ").strip()

    # JSON 数据文件路径
    if args.json:
        json_path = Path(args.json)
    else:
        json_path = project_root / "prebuilt_full.json"

    print("=" * 60)
    print("GenBFKit 数据库构建示例")
    print("=" * 60)

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

    # 1. 健康检查
    print("\n[1] 健康检查:")
    health = manager.health_check()
    print(f"  状态: {health.status}")
    print(f"  数据库已连接: {health.database_connected}")
    print(f"  元数据表存在: {health.metadata_tables_exist}")
    print(f"  JSON 文件有效: {health.json_file_valid}")

    # 2. 初始化数据库
    print("\n[2] 初始化数据库:")
    result = manager.initialize_database()
    if result["success"]:
        print("  [OK] 初始化成功")
    else:
        print(f"  [FAIL] 初始化失败: {result['message']}")

    # 3. 获取统计信息
    print("\n[3] 数据库统计:")
    stats = manager.get_statistics()
    print(f"  工种数量: {stats.total_work_types}")
    print(f"  数据类别: {stats.total_categories}")
    print(f"  数据集: {stats.total_datasets}")
    print(f"  物理表数: {stats.total_tables}")
    print(f"  总记录数: {stats.total_records}")

    # 4. 列出物理表
    print("\n[4] 物理表列表 (前 5 个):")
    tables = manager.list_tables()[:5]
    for table in tables:
        print(f"  - {table['table_name']} ({table['pool_type_zh']}, {table['row_count']} 行)")

    # 5. 获取数据池 Schema
    print("\n[5] 数据池类型:")
    from db_builder.services.schema_generator import SchemaGenerator
    from db_builder.models import AttributeTemplateModel

    session = manager.table_builder.get_session()
    try:
        templates = session.query(AttributeTemplateModel).all()
        pool_attrs_map = {t.pool_type: t.attributes for t in templates}
    finally:
        session.close()

    pool_schemas = SchemaGenerator.generate_all_pool_schemas(pool_attrs_map)
    for schema in pool_schemas:
        print(f"  - {schema['pool_type']} ({schema['pool_type_zh']}): {schema['column_count']} 列")

    # 6. 获取数据集树
    print("\n[6] 数据集层级结构 (前 2 个工种):")
    tree = manager.get_dataset_tree()[:2]
    for wt in tree:
        print(f"  {wt['work_type_en']} ({wt['work_type_zh']}):")
        for cat in wt.get('categories', [])[:2]:
            print(f"    - {cat['category_en']}")
            for pool in cat.get('pools', [])[:2]:
                print(f"      {pool['pool_type']} ({len(pool['datasets'])} 个数据集)")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
