"""
GenBFKit TSAT 快速参考指南
提供常用代码片段和最佳实践
"""

# ============================================
# 1. 导入模块
# ============================================

from time_scale_alignment_template import (
    TimeScaleAlignmentTemplate,
    TimeAlignmentConfig,
    TimestampNormalizer,
    InterpolationMethod,
    TimestampFormat
)

from postgresql_alignment_manager import (
    PostgreSQLAlignmentManager,
    DatabaseConfig
)

from datetime import datetime, timezone, timedelta


# ============================================
# 2. 时间戳标准化
# ============================================

# 基础使用
normalizer = TimestampNormalizer()

# 标准化 ISO8601 时间戳
iso_ts = "2024-01-15T10:30:00Z"
norm_ts = normalizer.normalize(iso_ts)
# 结果: datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)

# 标准化 Unix 时间戳（秒）
unix_ts = 1705318200
norm_ts = normalizer.normalize(unix_ts)

# 标准化 Unix 时间戳（毫秒）
unix_ms = 1705318200000
norm_ts = normalizer.normalize(unix_ms)

# 标准化数据库时间格式
db_ts = "2024-01-15 10:30:00"
norm_ts = normalizer.normalize(db_ts, default_timezone="Asia/Shanghai")

# 批量标准化
raw_timestamps = ["2024-01-15T10:30:00Z", "2024-01-15T10:30:05Z", 1705318210]
normalized = [normalizer.normalize(ts) for ts in raw_timestamps]


# ============================================
# 3. 时间序列对齐
# ============================================

# 创建配置
config = TimeAlignmentConfig(
    target_frequency="1S",                    # 1秒采样
    default_interpolation=InterpolationMethod.LINEAR,
    max_gap_seconds=60
)

# 创建对齐模板
tsat = TimeScaleAlignmentTemplate(config)

# 准备数据
timestamps = [
    datetime.now(timezone.utc) + timedelta(seconds=i*5)
    for i in range(10)
]
values = [1500.0 + i*0.5 for i in range(10)]

# 执行对齐
result = tsat.align_time_series(
    timestamps,
    values,
    table_name="temperature_sensor_01"
)

# 访问结果
aligned_timestamps = result.aligned_timestamps  # 对齐后的时间戳
aligned_values = result.aligned_values           # 对齐后的值
interpolated_count = result.interpolated_count  # 插值数量
missing_count = result.missing_count            # 缺失数量


# ============================================
# 4. 不同插值方法
# ============================================

# 线性插值（适用于连续值）
config_linear = TimeAlignmentConfig(
    target_frequency="1S",
    default_interpolation=InterpolationMethod.LINEAR
)

# 三次样条插值（适用于平滑曲线）
config_spline = TimeAlignmentConfig(
    target_frequency="1S",
    default_interpolation=InterpolationMethod.CUBIC_SPLINE
)

# 最近邻插值（适用于离散值）
config_nearest = TimeAlignmentConfig(
    target_frequency="1S",
    default_interpolation=InterpolationMethod.NEAREST
)

# 前向填充
config_ffill = TimeAlignmentConfig(
    target_frequency="1S",
    default_interpolation=InterpolationMethod.FORWARD_FILL,
    max_gap_seconds=30  # 只填充30秒内的缺失
)


# ============================================
# 5. 多源时间同步
# ============================================

# 准备多个数据源
sources = {
    "PLC_System": (
        [datetime.now(timezone.utc) + timedelta(seconds=i*5) for i in range(20)],
        [1500 + i*0.1 for i in range(20)]
    ),
    "DCS_System": (
        [datetime.now(timezone.utc) + timedelta(seconds=2 + i*5) for i in range(20)],
        [1499.5 + i*0.1 for i in range(20)]
    )
}

# 计算时间偏移
tsat = TimeScaleAlignmentTemplate(TimeAlignmentConfig(target_frequency="5S"))
offsets = tsat.synchronize_multiple_sources(sources)

# 应用偏移
for source, offset in offsets.items():
    if abs(offset) > 0.1:
        timestamps = sources[source][0]
        corrected = [ts - timedelta(seconds=offset) for ts in timestamps]
        sources[source] = (corrected, sources[source][1])


# ============================================
# 6. PostgreSQL 集成
# ============================================

# 配置数据库
db_config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="genbfkit",
    user="postgres",
    password="your_password"
)

# 创建管理器
with PostgreSQLAlignmentManager(
    db_config,
    TimeAlignmentConfig(target_frequency="1S")
) as manager:
    # 初始化表结构
    manager.setup_metadata_tables()

    # 对齐单个表
    results = manager.align_table_data(
        table_name="blast_furnace_temp_001",
        timestamp_column="timestamp",
        batch_id="batch_20240115"
    )

    # 获取表的对齐配置
    config_dict = manager.get_table_alignment_config("blast_furnace_temp_001")

    # 更新表的对齐配置
    manager.update_table_alignment_config(
        "blast_furnace_temp_001",
        {
            "time_alignment_strategy": "LINEAR",
            "default_timezone": "UTC",
            "sampling_interval_seconds": 5.0
        }
    )


# ============================================
# 7. 批量处理多张表
# ============================================

def batch_align_tables(
    manager: PostgreSQLAlignmentManager,
    table_names: list,
    batch_prefix: str
):
    """批量对齐多张表"""
    results_summary = {}

    for i, table_name in enumerate(table_names):
        batch_id = f"{batch_prefix}_{i:03d}"

        try:
            logger.info(f"处理表 {i+1}/{len(table_names)}: {table_name}")
            results = manager.align_table_data(
                table_name=table_name,
                batch_id=batch_id
            )

            results_summary[table_name] = {
                "batch_id": batch_id,
                "status": "success",
                "columns": list(results.keys())
            }

        except Exception as e:
            logger.error(f"表 {table_name} 处理失败: {e}")
            results_summary[table_name] = {
                "batch_id": batch_id,
                "status": "failed",
                "error": str(e)
            }

    return results_summary


# 使用示例
with PostgreSQLAlignmentManager(
    db_config,
    TimeAlignmentConfig(target_frequency="5S")
) as manager:
    table_names = [
        "blast_furnace_temp_001",
        "blast_furnace_temp_002",
        "blast_furnace_pressure_001"
    ]

    summary = batch_align_tables(
        manager,
        table_names,
        batch_prefix="batch_20240115"
    )


# ============================================
# 8. 数据质量评估
# ============================================

# ============================================
# 9. 导出对齐结果
# ============================================

import pandas as pd

def export_alignment_result(result, output_path: str):
    """导出对齐结果到 CSV"""
    df = pd.DataFrame({
        "timestamp": result.aligned_timestamps,
        "value": result.aligned_values,
        "is_interpolated": [
            True if val is None else False
            for val in result.aligned_values
        ]
    })

    df.to_csv(output_path, index=False)
    logger.info(f"对齐结果已导出到: {output_path}")


# ============================================
# 10. 可视化对齐效果
# ============================================

import matplotlib.pyplot as plt

def plot_alignment_comparison(
    original_timestamps,
    original_values,
    aligned_timestamps,
    aligned_values,
    output_path: str
):
    """绘制对齐前后对比图"""
    fig, ax = plt.subplots(figsize=(14, 6))

    # 原始数据
    ax.plot(
        original_timestamps,
        original_values,
        'o-',
        label='原始数据',
        markersize=8,
        linewidth=1.5
    )

    # 对齐后数据
    ax.plot(
        aligned_timestamps,
        aligned_values,
        's-',
        label='对齐后数据',
        markersize=4,
        linewidth=1,
        alpha=0.7
    )

    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('值', fontsize=12)
    ax.set_title('数据对齐效果对比', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


# ============================================
# 11. 常见场景
# ============================================

# 场景1: 处理缺失值
def handle_missing_values(config):
    """处理缺失值的配置"""
    return TimeAlignmentConfig(
        target_frequency="1S",
        default_interpolation=InterpolationMethod.FORWARD_FILL,
        max_gap_seconds=30  # 只填充30秒内的缺失
    )


# 场景2: 高频采样数据
def high_frequency_data(config):
    """高频采样数据的配置"""
    return TimeAlignmentConfig(
        target_frequency="100ms",  # 100毫秒
        default_interpolation=InterpolationMethod.CUBIC_SPLINE,
        max_gap_seconds=5
    )


# 场景3: 低频采样数据
def low_frequency_data(config):
    """低频采样数据的配置"""
    return TimeAlignmentConfig(
        target_frequency="1M",  # 1分钟
        default_interpolation=InterpolationMethod.LINEAR,
        max_gap_seconds=600  # 允许更大的间隔
    )


# ============================================
# 12. 错误处理
# ============================================

def safe_normalize_timestamp(raw_ts, normalizer):
    """安全的时间戳标准化（带错误处理）"""
    try:
        return normalizer.normalize(raw_ts)
    except Exception as e:
        logger.error(f"时间戳标准化失败: {raw_ts}, 错误: {e}")
        return None


def safe_align_table(manager, table_name, max_retries=3):
    """安全的表对齐（带重试）"""
    for attempt in range(max_retries):
        try:
            results = manager.align_table_data(table_name)
            return results
        except Exception as e:
            logger.warning(
                f"表 {table_name} 对齐失败 (尝试 {attempt+1}/{max_retries}): {e}"
            )
            if attempt == max_retries - 1:
                logger.error(f"表 {table_name} 对齐最终失败")
                raise


# ============================================
# 13. 性能优化
# ============================================

# 使用批量插入（在 PostgreSQL 集成中已实现）
# 使用索引（已自动创建）
# 分批处理大数据集

def process_large_table_in_batches(
    manager,
    table_name,
    batch_size=10000
):
    """分批处理大表"""
    # 读取表的总行数
    with manager.connection.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cur.fetchone()[0]

    logger.info(f"表 {table_name} 共 {total_rows} 行，开始分批处理")

    # 分批处理
    for offset in range(0, total_rows, batch_size):
        logger.info(f"处理行 {offset} - {min(offset+batch_size, total_rows)}")
        # 读取当前批次
        timestamps, values = manager.read_raw_data(
            table_name,
            limit=batch_size
        )
        # 对齐当前批次
        # ... 对齐逻辑


# ============================================
# 14. 监控和日志
# ============================================

def setup_logging(log_file="/app/work/logs/bypass/time_alignment.log"):
    """配置日志"""
    import logging
    from logging.handlers import RotatingFileHandler

    logger = logging.getLogger("TSAT")
    logger.setLevel(logging.INFO)

    # 文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ============================================
# 15. 快速测试
# ============================================

def quick_test():
    """快速测试功能"""
    print("开始快速测试...")

    # 测试1: 时间戳标准化
    normalizer = TimestampNormalizer()
    ts = normalizer.normalize("2024-01-15T10:30:00Z")
    print(f"✓ 时间戳标准化: {ts}")

    # 测试2: 时间序列对齐
    config = TimeAlignmentConfig(target_frequency="1S")
    tsat = TimeScaleAlignmentTemplate(config)

    timestamps = [datetime.now(timezone.utc) + timedelta(seconds=i*5) for i in range(5)]
    values = [1500 + i for i in range(5)]

    result = tsat.align_time_series(timestamps, values, "test")
    print(f"✓ 时间序列对齐: {len(result.aligned_timestamps)} 个点")

    print("\n快速测试完成！")


if __name__ == "__main__":
    quick_test()
