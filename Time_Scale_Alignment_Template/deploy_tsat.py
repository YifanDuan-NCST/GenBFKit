#!/usr/bin/env python3
"""
GenBFKit TSAT 部署脚本
用于将时间尺度对齐模板集成到现有 GenBFKit 数据库中
"""

import os
import sys
import logging
import json
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖是否安装"""
    logger.info("检查依赖包...")

    required_packages = [
        "numpy",
        "scipy",
        "pandas",
        "psycopg2-binary",
        "matplotlib"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            logger.info(f"  ✓ {package}")
        except ImportError:
            logger.warning(f"  ✗ {package} (未安装)")
            missing_packages.append(package)

    if missing_packages:
        logger.error(f"\n缺少 {len(missing_packages)} 个依赖包")
        logger.info("安装命令:")
        logger.info(f"  uv add {' '.join(missing_packages)}")
        return False

    logger.info("\n✓ 所有依赖已安装")
    return True


def load_config(config_path: str = "config_time_alignment.json") -> dict:
    """加载配置文件"""
    logger.info(f"加载配置文件: {config_path}")

    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在: {config_path}")
        logger.info("将使用默认配置")
        return get_default_config()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("✓ 配置文件加载成功")
        return config
    except Exception as e:
        logger.error(f"配置文件加载失败: {e}")
        logger.info("将使用默认配置")
        return get_default_config()


def get_default_config() -> dict:
    """获取默认配置"""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "genbfkit",
            "user": "postgres",
            "password": "your_password_here",
            "schema": "public"
        },
        "time_alignment": {
            "target_timezone": "UTC",
            "target_frequency": "1s",
            "default_interpolation": "LINEAR",
            "max_gap_seconds": 300
        },
        "logging": {
            "level": "INFO"
        }
    }


def test_database_connection(config: dict) -> bool:
    """测试数据库连接"""
    logger.info("测试数据库连接...")

    try:
        import psycopg2

        db_config = config["database"]
        connection = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"]
        )
        connection.close()
        logger.info("✓ 数据库连接成功")
        return True

    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {e}")
        logger.info("\n请检查:")
        logger.info("  1. PostgreSQL 服务是否启动")
        logger.info("  2. 数据库配置是否正确")
        logger.info("  3. 用户名和密码是否正确")
        return False


def check_genbfkit_tables(config: dict) -> bool:
    """检查 GenBFKit 元数据表是否存在"""
    logger.info("检查 GenBFKit 元数据表...")

    try:
        import psycopg2

        db_config = config["database"]
        connection = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"]
        )

        with connection.cursor() as cur:
            # 检查核心元数据表
            required_tables = [
                '"Base dictionary"',
                '"Data category dictionary"',
                '"Data pool dictionary"',
                '"Dataset dictionary"',
                '"Data attribute dictionary"'
            ]

            missing_tables = []

            for table in required_tables:
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = {table.replace('"', "'")}
                    );
                """)
                exists = cur.fetchone()[0]

                if exists:
                    logger.info(f"  ✓ {table}")
                else:
                    logger.warning(f"  ✗ {table}")
                    missing_tables.append(table)

            connection.close()

        if missing_tables:
            logger.warning(f"\n缺少 {len(missing_tables)} 个元数据表")
            logger.warning("请确保 GenBFKit 框架已正确部署")
            return False

        logger.info("\n✓ 所有元数据表已就绪")
        return True

    except Exception as e:
        logger.error(f"检查失败: {e}")
        return False


def setup_tsat_tables(config: dict) -> bool:
    """初始化 TSAT 扩展表"""
    logger.info("初始化 TSAT 扩展表...")

    try:
        from postgresql_alignment_manager import (
            PostgreSQLAlignmentManager,
            DatabaseConfig,
            TimeAlignmentConfig
        )
        from time_scale_alignment_template import InterpolationMethod

        # 创建配置对象
        db_config = DatabaseConfig(**config["database"])
        time_config = TimeAlignmentConfig(
            target_timezone=config["time_alignment"]["target_timezone"],
            target_frequency=config["time_alignment"]["target_frequency"],
            default_interpolation=InterpolationMethod(
                config["time_alignment"]["default_interpolation"]
            ),
            max_gap_seconds=config["time_alignment"]["max_gap_seconds"]
        )

        # 创建管理器并设置表
        with PostgreSQLAlignmentManager(db_config, time_config) as manager:
            manager.setup_metadata_tables()

        logger.info("✓ TSAT 扩展表初始化成功")
        return True

    except Exception as e:
        logger.error(f"✗ TSAT 扩展表初始化失败: {e}")
        return False


def run_demo(config: dict):
    """运行演示"""
    logger.info("\n运行演示...")

    try:
        from usage_examples import example_1_timestamp_normalization

        logger.info("\n运行示例1: 时间戳标准化")
        example_1_timestamp_normalization()

        logger.info("\n✓ 演示完成")
        return True

    except Exception as e:
        logger.error(f"演示运行失败: {e}")
        return False


def print_summary():
    """打印部署摘要"""
    print("\n" + "=" * 70)
    print("GenBFKit TSAT 部署摘要")
    print("=" * 70)

    print("\n已创建的文件:")
    print("  1. time_scale_alignment_template.py      - 核心算法模块")
    print("  2. postgresql_alignment_manager.py       - PostgreSQL集成模块")
    print("  3. usage_examples.py                     - 使用示例集合")
    print("  4. config_time_alignment.json            - 配置文件")
    print("  5. README_TSAT.md                        - 技术文档")
    print("  6. deploy_tsat.py                        - 本部署脚本")

    print("\n数据库扩展:")
    print("  1. 扩展 'Data attribute dictionary' 表")
    print("  2. 新增 'time_alignment_log' 表")
    print("  3. 新增 'time_alignment_batch_summary' 表")

    print("\n核心功能:")
    print("  1. 时间戳标准化 - 支持 ISO8601、Unix时间戳等")
    print("  2. 时间轴对齐 - 统一采样频率")
    print("  3. 自适应插值 - 线性、样条、最近邻等方法")
    print("  4. 多源同步 - 自动计算时间偏移")
    print("  5. 异常检测 - 基于3σ原则的异常值识别")

    print("\n快速开始:")
    print("  1. 查看示例: uv run python usage_examples.py")
    print("  2. 阅读文档: cat README_TSAT.md")
    print("  3. 修改配置: 编辑 config_time_alignment.json")

    print("\n技术支持:")
    print("  - 文档: README_TSAT.md")
    print("  - 日志: /app/work/logs/bypass/time_alignment.log")

    print("\n" + "=" * 70)


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("GenBFKit 时间尺度对齐模板 (TSAT) 部署工具")
    print("=" * 70)

    # 步骤1: 检查依赖
    print("\n[步骤 1/5] 检查依赖包")
    if not check_dependencies():
        logger.error("依赖检查失败，请先安装缺失的包")
        sys.exit(1)

    # 步骤2: 加载配置
    print("\n[步骤 2/5] 加载配置")
    config = load_config()

    # 步骤3: 测试数据库连接
    print("\n[步骤 3/5] 测试数据库连接")
    if not test_database_connection(config):
        logger.error("数据库连接测试失败")
        logger.info("请修改 config_time_alignment.json 中的数据库配置后重试")
        sys.exit(1)

    # 步骤4: 检查 GenBFKit 表
    print("\n[步骤 4/5] 检查 GenBFKit 元数据表")
    if not check_genbfkit_tables(config):
        logger.warning("GenBFKit 元数据表检查未通过")
        logger.info("将继续尝试初始化 TSAT 扩展表...")

    # 步骤5: 初始化 TSAT 表
    print("\n[步骤 5/5] 初始化 TSAT 扩展表")
    if not setup_tsat_tables(config):
        logger.error("TSAT 扩展表初始化失败")
        sys.exit(1)

    # 运行演示（可选）
    print("\n[可选] 运行演示")
    response = input("是否运行演示？(y/n): ").strip().lower()
    if response == 'y':
        run_demo(config)

    # 打印摘要
    print_summary()

    logger.info("\n✓ 部署完成！")
    logger.info("感谢使用 GenBFKit 时间尺度对齐模板")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n部署已取消")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n部署失败: {e}", exc_info=True)
        sys.exit(1)
