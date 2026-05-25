# -*- coding: utf-8 -*-
"""初始化数据库脚本"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from db_builder.services.database_manager import DatabaseManager
from db_builder.config import DatabaseSettings


def main():
    parser = argparse.ArgumentParser(description="GenBFKit 数据库初始化工具")
    parser.add_argument("--host", type=str, default="localhost", help="Database host")
    parser.add_argument("--port", "-p", type=int, default=5432, help="Database port")
    parser.add_argument("--database", "-d", type=str, default="genbfkit", help="Database name")
    parser.add_argument("--username", "-u", type=str, default="postgres", help="Database username")
    parser.add_argument("--password", "-w", type=str, default=None, help="Database password")
    parser.add_argument("--json", "-j", type=str, default=None, help="JSON data file path")
    parser.add_argument("--skip-import", action="store_true", help="Skip JSON import (only create tables)")

    args = parser.parse_args()

    # 获取密码
    password = args.password or os.environ.get("GENBFKIT__DATABASE__PASSWORD", "")
    if not password:
        password = input("Enter database password: ").strip()

    print("=" * 60)
    print("GenBFKit Database Initialization Tool")
    print("=" * 60)

    db_settings = DatabaseSettings(
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=password,
    )

    if args.json:
        json_path_input = Path(args.json)
        if json_path_input.is_absolute():
            json_path = json_path_input
        else:
            json_path = project_root / json_path_input
    else:
        json_path = project_root / "prebuilt_full.json"

    print(f"\nDatabase config:")
    print(f"  Host: {db_settings.host}:{db_settings.port}")
    print(f"  Database: {db_settings.database}")
    print(f"  User: {db_settings.username}")
    print(f"\nJSON file: {json_path}")

    if not json_path.exists():
        print(f"\nError: JSON file not found: {json_path}")
        return False

    manager = DatabaseManager(db_settings=db_settings, json_path=json_path)

    # Health check
    print("\n[1/3] Checking database connection...")
    health = manager.health_check()
    print(f"  Status: {health.status}")
    print(f"  Message: {health.message}")

    if not health.database_connected:
        print("\nError: Cannot connect to database!")
        print("Tip: Make sure PostgreSQL is running and credentials are correct")
        return False

    # Initialize
    print("\n[2/3] Initializing database...")
    result = manager.initialize_database()

    if result["success"]:
        print("  [OK] Database initialized")
        for step in result["steps"]:
            status = "[OK]" if step["success"] else "[WARN]"
            msg = step.get("message", "")
            print(f"  {status} {step['step']}: {msg}")
    else:
        print("  [FAIL] Initialization failed")
        for step in result["steps"]:
            if not step["success"]:
                print(f"    - {step['message']}")

    # Get stats
    print("\n[3/3] Getting statistics...")
    stats = manager.get_statistics()
    print(f"  Work types: {stats.total_work_types}")
    print(f"  Categories: {stats.total_categories}")
    print(f"  Data pools: {stats.total_pools}")
    print(f"  Datasets: {stats.total_datasets}")
    print(f"  Attribute templates: {stats.total_attribute_templates}")
    print(f"  Physical tables: {stats.total_tables}")

    print("\n" + "=" * 60)
    print("Initialization complete!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    main()
