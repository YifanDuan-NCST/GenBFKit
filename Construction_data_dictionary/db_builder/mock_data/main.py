# -*- coding: utf-8 -*-
"""
Mock Data Generator - CLI 入口脚本
独立运行，不依赖包安装：
    python db_builder/mock_data/main.py --rows 100
或（需先安装包）：
    python -m db_builder.mock_data.main --rows 100
"""

import sys
import os
from pathlib import Path

# 将项目根目录加入 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db_builder.mock_data.generator import MockDataGenerator, GenerationStats
from datetime import datetime


def main():
    import argparse

    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="GenBFKit Mock Data Generator - 为所有物理表生成虚拟数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python db_builder/mock_data/main.py                    # 生成所有表，每表100行
  python db_builder/mock_data/main.py --rows 50          # 每表50行
  python db_builder/mock_data/main.py --mode overwrite   # 先清空再插入
  python db_builder/mock_data/main.py --max 10           # 仅测试前10张表
  python db_builder/mock_data/main.py --seed 42         # 使用固定种子(可复现)
  python db_builder/mock_data/main.py --quiet           # 静默模式
        """
    )
    parser.add_argument(
        "--rows", "-r", type=int, default=100,
        help="每个物理表生成的行数 (默认: 100)"
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=None,
        help="随机数种子，用于生成可复现的测试数据 (默认: None=每次不同)"
    )
    parser.add_argument(
        "--mode", "-m", choices=["upsert", "overwrite"], default="upsert",
        help="upsert=已有满N行则跳过; overwrite=先清空再插入 (默认: upsert)"
    )
    parser.add_argument(
        "--max", "-n", type=int, default=None,
        help="最多处理的表数量，用于快速测试 (默认: None=全部)"
    )
    parser.add_argument(
        "--batch", "-b", type=int, default=500,
        help="每批插入的行数 (默认: 500)"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="静默模式，仅输出最终报告"
    )

    args = parser.parse_args()

    # 打印启动信息
    print()
    print("=" * 60)
    print("  GenBFKit Mock Data Generator")
    print("  高炉炼铁开源数据整合框架 - 虚拟数据生成器")
    print("=" * 60)
    print(f"  目标行数/表:    {args.rows}")
    print(f"  生成模式:       {args.mode}")
    print(f"  随机种子:       {args.seed if args.seed else '随机'}")
    print(f"  最大表数:       {args.max if args.max else '全部'}")
    print(f"  批处理大小:     {args.batch}")
    print("-" * 60)
    print()

    # 初始化生成器
    generator = MockDataGenerator(
        rows_per_table=args.rows,
        seed=args.seed,
    )

    # 进度回调
    def progress(table_name: str, idx: int, total: int):
        if not args.quiet:
            pct = idx / total * 100
            bar_width = 30
            filled = int(bar_width * idx / total)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(
                f"\r  [{bar}] {pct:5.1f}%  ({idx}/{total})  {table_name[:40]}",
                end="",
                flush=True
            )

    start_time = datetime.now()
    stats = generator.generate_all(
        mode=args.mode,
        batch_size=args.batch,
        max_tables=args.max,
        progress_callback=progress,
    )
    elapsed = (datetime.now() - start_time).total_seconds()

    # 输出报告
    print()
    print()
    print("=" * 60)
    print("  生成报告")
    print("=" * 60)
    print(f"  耗时:            {elapsed:.1f} 秒")
    print(f"  总表数:          {stats.total_tables}")
    print(f"  成功生成:        {stats.tables_with_data} 张表")
    print(f"  跳过(已满):     {stats.tables_skipped} 张表")
    print(f"  失败:            {stats.tables_failed} 张表")
    print(f"  总生成行数:      {stats.total_rows_generated:,} 行")

    if stats.errors:
        print()
        print(f"  失败详情 (共 {len(stats.errors)} 条):")
        for err in stats.errors[:10]:
            print(f"    [FAIL] {err}")
        if len(stats.errors) > 10:
            print(f"    ... 还有 {len(stats.errors) - 10} 条错误")

    if not args.quiet and stats.errors:
        print()
        print("  建议: 查看 db_builder/mock_data/README.md 了解错误详情")

    print("=" * 60)
    print()
    print("  生成完成！生成的虚拟数据可通过 Web 界面查看。")
    print("  访问: http://localhost:8000/")
    print()


if __name__ == "__main__":
    main()
