"""
GenBFKit 时间尺度对齐模板 - 完整使用示例
展示在实际高炉工况数据场景中的应用
"""

import logging
from datetime import datetime, timezone, timedelta
import random
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict

from time_scale_alignment_template import (
    TimeScaleAlignmentTemplate,
    TimeAlignmentConfig,
    InterpolationMethod,
    TimestampFormat,
    TimestampNormalizer
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def simulate_blast_furnace_data(
    sensor_count: int = 3,
    duration_minutes: int = 10,
    base_temp: float = 1500.0,
    noise_level: float = 5.0
) -> Dict[str, Dict]:
    """
    模拟高炉工况数据

    Args:
        sensor_count: 传感器数量
        duration_minutes: 持续时间（分钟）
        base_temp: 基础温度
        noise_level: 噪声水平

    Returns:
        Dict[str, Dict]: 模拟数据字典
    """
    logger.info(f"生成模拟高炉数据: {sensor_count}个传感器, {duration_minutes}分钟")

    data = {}

    # 传感器配置
    sensors = {
        "temperature": {"base": base_temp, "freq": 2, "noise": noise_level},
        "pressure": {"base": 3.5, "freq": 5, "noise": 0.1},
        "flow_rate": {"base": 1200.0, "freq": 10, "noise": 50.0}
    }

    # 生成不同采样频率的数据
    for sensor_name, config in sensors.items():
        timestamps = []
        values = []

        current_time = datetime.now(timezone.utc)
        end_time = current_time + timedelta(minutes=duration_minutes)

        interval_seconds = config["freq"]  # 采样间隔（秒）
        num_points = int(duration_minutes * 60 / interval_seconds)

        for i in range(num_points):
            ts = current_time + timedelta(seconds=i * interval_seconds)

            # 添加随机延迟（模拟真实场景）
            delay = random.uniform(-0.5, 0.5)
            ts = ts + timedelta(seconds=delay)

            # 生成带噪声的值
            noise = random.gauss(0, config["noise"])
            # 添加趋势
            trend = 10 * (i / num_points)  # 线性增长趋势
            value = config["base"] + trend + noise

            # 偶尔添加异常值
            if random.random() < 0.02:  # 2%的异常值
                value += random.uniform(20, 50)

            timestamps.append(ts)
            values.append(value)

        data[sensor_name] = {
            "timestamps": timestamps,
            "values": values,
            "sampling_interval": interval_seconds
        }

    return data


def example_1_timestamp_normalization():
    """示例1: 时间戳标准化"""
    print("\n" + "=" * 70)
    print("示例1: 时间戳标准化")
    print("=" * 70)

    # 不同来源的时间戳格式
    raw_timestamps = {
        "source_a": ["2024-01-15T10:30:00Z", "2024-01-15T10:30:05Z", "2024-01-15T10:30:10Z"],
        "source_b": [1705318200, 1705318205, 1705318210],  # Unix时间戳
        "source_c": ["2024-01-15 10:30:00", "2024-01-15 10:30:05", "2024-01-15 10:30:10"],
        "source_d": [1705318200000, 1705318205000, 1705318210000],  # 毫秒时间戳
    }

    normalizer = TimestampNormalizer()

    print("\n原始时间戳:")
    for source, ts_list in raw_timestamps.items():
        print(f"  {source}: {ts_list}")

    print("\n标准化后:")
    normalized = {}
    for source, ts_list in raw_timestamps.items():
        normalized[source] = []
        for ts in ts_list:
            try:
                norm_ts = normalizer.normalize(ts)
                normalized[source].append(norm_ts.strftime("%Y-%m-%d %H:%M:%S UTC"))
            except Exception as e:
                print(f"  {source}[{ts}] 标准化失败: {e}")

    for source, ts_list in normalized.items():
        print(f"  {source}: {ts_list}")

    print("\n✓ 时间戳标准化完成")


def example_2_time_series_alignment():
    """示例2: 时间序列对齐"""
    print("\n" + "=" * 70)
    print("示例2: 时间序列对齐")
    print("=" * 70)

    # 生成模拟数据
    data = simulate_blast_furnace_data(
        sensor_count=3,
        duration_minutes=5,
        base_temp=1500.0
    )

    # 创建对齐配置
    config = TimeAlignmentConfig(
        target_frequency="1S",  # 对齐到1秒
        default_interpolation=InterpolationMethod.LINEAR,
        max_gap_seconds=10
    )

    tsat = TimeScaleAlignmentTemplate(config)

    print(f"\n模拟数据:")
    for sensor_name, sensor_data in data.items():
        print(f"  {sensor_name}:")
        print(f"    - 采样点数: {len(sensor_data['timestamps'])}")
        print(f"    - 采样间隔: {sensor_data['sampling_interval']}秒")
        print(f"    - 前3个值: {sensor_data['values'][:3]}")

    # 对齐每个传感器的数据
    print(f"\n执行时间对齐（目标频率: {config.target_frequency}）...")
    aligned_data = {}

    for sensor_name, sensor_data in data.items():
        result = tsat.align_time_series(
            sensor_data["timestamps"],
            sensor_data["values"],
            table_name=f"sensor_{sensor_name}"
        )

        aligned_data[sensor_name] = result

        print(f"\n  {sensor_name} 对齐结果:")
        print(f"    - 原始数据点: {len(sensor_data['timestamps'])}")
        print(f"    - 对齐后数据点: {len(result.aligned_timestamps)}")
        print(f"    - 插值数量: {result.interpolated_count}")
        print(f"    - 缺失数量: {result.missing_count}")
        print(f"    - 前5个对齐值: {[f'{v:.2f}' if v else 'NULL' for v in result.aligned_values[:5]]}")

    print("\n✓ 时间序列对齐完成")


def example_3_multi_source_synchronization():
    """示例3: 多源时间同步"""
    print("\n" + "=" * 70)
    print("示例3: 多源时间同步")
    print("=" * 70)

    # 模拟3个数据源，时间有不同偏移
    base_time = datetime.now(timezone.utc)

    sources = {
        "PLC_System": {
            "timestamps": [base_time + timedelta(seconds=i*5) for i in range(20)],
            "values": [1500 + i*0.1 for i in range(20)]
        },
        "DCS_System": {
            # DCS系统有2秒延迟
            "timestamps": [base_time + timedelta(seconds=2 + i*5) for i in range(20)],
            "values": [1499.5 + i*0.1 for i in range(20)]
        },
        "SCADA_System": {
            # SCADA系统有-1秒偏移（时钟快1秒）
            "timestamps": [base_time + timedelta(seconds=-1 + i*5) for i in range(20)],
            "values": [1500.5 + i*0.1 for i in range(20)]
        }
    }

    config = TimeAlignmentConfig(target_frequency="5S")
    tsat = TimeScaleAlignmentTemplate(config)

    print("\n各数据源:")
    for name, data in sources.items():
        print(f"  {name}: {len(data['timestamps'])} 个数据点")
        print(f"    开始时间: {data['timestamps'][0].strftime('%H:%M:%S')}")
        print(f"    结束时间: {data['timestamps'][-1].strftime('%H:%M:%S')}")

    # 计算时间偏移
    print("\n计算时间偏移...")
    offsets = tsat.synchronize_multiple_sources(
        {name: (data["timestamps"], data["values"]) for name, data in sources.items()}
    )

    print("\n时间偏移结果:")
    for source, offset in offsets.items():
        print(f"  {source}: {offset:+.4f} 秒")

    # 应用偏移
    print("\n应用时间偏移...")
    for source, offset in offsets.items():
        if abs(offset) > 0.1:  # 只处理有明显偏移的源
            sources[source]["timestamps"] = [
                ts - timedelta(seconds=offset)
                for ts in sources[source]["timestamps"]
            ]
            print(f"  ✓ {source} 时间戳已校正 {offset:+.4f} 秒")

    print("\n✓ 多源时间同步完成")


def example_4_visualize_alignment():
    """示例4: 可视化对齐效果"""
    print("\n" + "=" * 70)
    print("示例4: 可视化对齐效果")
    print("=" * 70)

    # 生成模拟数据
    data = simulate_blast_furnace_data(
        sensor_count=1,
        duration_minutes=2,
        base_temp=1500.0
    )

    # 配置不同采样频率
    sensor_name = "temperature"
    original_timestamps = data[sensor_name]["timestamps"]
    original_values = data[sensor_name]["values"]

    # 创建对齐配置（将5秒采样对齐到1秒）
    config = TimeAlignmentConfig(
        target_frequency="1S",
        default_interpolation=InterpolationMethod.LINEAR
    )

    tsat = TimeScaleAlignmentTemplate(config)
    result = tsat.align_time_series(
        original_timestamps,
        original_values,
        table_name="temperature_sensor"
    )

    print(f"\n原始数据: {len(original_values)} 个点")
    print(f"对齐后数据: {len(result.aligned_values)} 个点")

    # 创建可视化
    try:
        # 配置中文字体
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False

        fig, axes = plt.subplots(2, 1, figsize=(14, 10))

        # 图1: 原始数据 vs 对齐后数据
        ax1 = axes[0]
        ax1.plot(
            original_timestamps,
            original_values,
            'o-',
            label='Original Data (5s sampling)',
            markersize=8,
            linewidth=1.5
        )
        ax1.plot(
            result.aligned_timestamps,
            result.aligned_values,
            's-',
            label='Aligned Data (1s sampling)',
            markersize=3,
            linewidth=1,
            alpha=0.7
        )
        ax1.set_xlabel('Time', fontsize=12)
        ax1.set_ylabel('Temperature (°C)', fontsize=12)
        ax1.set_title('Comparison: Original vs Aligned Data', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)

        # 图2: 放大显示插值区域
        ax2 = axes[1]

        # 选择中间一段数据放大
        start_idx = len(result.aligned_timestamps) // 2 - 10
        end_idx = start_idx + 20

        zoom_timestamps = result.aligned_timestamps[start_idx:end_idx]
        zoom_values = result.aligned_values[start_idx:end_idx]

        ax2.plot(
            zoom_timestamps,
            zoom_values,
            'o-',
            label='Aligned Data',
            markersize=6,
            linewidth=2
        )

        # 标记插值点
        for i, val in enumerate(zoom_values):
            ts = zoom_timestamps[i]
            # 检查是否是原始数据点（简化判断）
            is_original = any(abs((ts - orig_ts).total_seconds()) < 0.1
                           for orig_ts in original_timestamps)

            if not is_original:
                ax2.plot(ts, val, 'rs', markersize=10, alpha=0.5,
                        label='Interpolated Points' if i == start_idx + 1 else '')

        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Temperature (°C)', fontsize=12)
        ax2.set_title('Zoomed View: Interpolation Effect', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存图像
        output_path = "/workspace/projects/alignment_visualization.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\n✓ 可视化图表已保存到: {output_path}")

        plt.close()

    except ImportError:
        print("\n⚠ matplotlib 未安装，跳过可视化")
        print("  安装命令: uv add matplotlib")


def example_5_complete_workflow():
    """示例5: 完整工作流程"""
    print("\n" + "=" * 70)
    print("示例5: 完整工作流程")
    print("=" * 70)

    # 模拟场景：从3个不同数据源导入高炉工况数据
    print("\n场景描述:")
    print("  - 数据源1: PLC系统 (2秒采样)")
    print("  - 数据源2: DCS系统 (5秒采样, 有2秒延迟)")
    print("  - 数据源3: 历史数据库 (10秒采样)")

    # 步骤1: 生成模拟数据
    print("\n[步骤1] 生成模拟数据...")
    data_sources = {}

    # PLC数据
    base_time = datetime.now(timezone.utc)
    data_sources["PLC"] = {
        "timestamps": [base_time + timedelta(seconds=i*2) for i in range(30)],
        "values": [1500 + i*0.5 + random.gauss(0, 2) for i in range(30)],
        "format": "ISO8601"
    }

    # DCS数据（有延迟）
    data_sources["DCS"] = {
        "timestamps": [base_time + timedelta(seconds=2 + i*5) for i in range(12)],
        "values": [1498 + i*1.2 + random.gauss(0, 3) for i in range(12)],
        "format": "UNIX"
    }

    # 历史数据库数据
    data_sources["Historical"] = {
        "timestamps": [base_time + timedelta(seconds=i*10) for i in range(6)],
        "values": [1502 + i*2.5 + random.gauss(0, 5) for i in range(6)],
        "format": "DATABASE_DATETIME"
    }

    for name, data in data_sources.items():
        print(f"  {name}: {len(data['timestamps'])} 个数据点, 格式={data['format']}")

    # 步骤2: 标准化时间戳
    print("\n[步骤2] 标准化时间戳...")

    for name, data in data_sources.items():
        # 时间戳已经是 datetime 对象，直接使用
        data["normalized_timestamps"] = data["timestamps"]

        print(f"  {name}: 时间戳已标准化")
        print(f"    开始: {data['normalized_timestamps'][0].strftime('%H:%M:%S')}")
        print(f"    结束: {data['normalized_timestamps'][-1].strftime('%H:%M:%S')}")

    # 步骤3: 多源时间同步
    print("\n[步骤3] 多源时间同步...")
    config = TimeAlignmentConfig(target_frequency="1S")
    tsat = TimeScaleAlignmentTemplate(config)

    offsets = tsat.synchronize_multiple_sources({
        name: (data["normalized_timestamps"], data["values"])
        for name, data in data_sources.items()
    })

    print("  时间偏移量:")
    for source, offset in offsets.items():
        print(f"    {source}: {offset:+.4f} 秒")

    # 步骤4: 应用偏移并合并数据
    print("\n[步骤4] 合并所有数据源...")
    all_timestamps = []
    all_values = []

    for name, data in data_sources.items():
        offset = offsets.get(name, 0)
        for ts, val in zip(data["normalized_timestamps"], data["values"]):
            corrected_ts = ts - timedelta(seconds=offset)
            all_timestamps.append(corrected_ts)
            all_values.append(val)

    # 按时间排序
    combined = list(zip(all_timestamps, all_values))
    combined.sort(key=lambda x: x[0])
    all_timestamps, all_values = zip(*combined)

    print(f"  合并后数据点: {len(all_timestamps)}")

    # 步骤5: 时间轴对齐
    print("\n[步骤5] 时间轴对齐到统一频率...")
    result = tsat.align_time_series(
        list(all_timestamps),
        list(all_values),
        table_name="merged_blast_furnace_data"
    )

    print(f"  对齐结果:")
    print(f"    - 原始数据点: {len(all_timestamps)}")
    print(f"    - 对齐后数据点: {len(result.aligned_timestamps)}")
    print(f"    - 插值数量: {result.interpolated_count}")
    print(f"    - 缺失数量: {result.missing_count}")

    # 步骤6: 导出对齐结果
    print("\n[步骤6] 导出对齐结果...")

    # 创建DataFrame
    df = pd.DataFrame({
        "timestamp": result.aligned_timestamps,
        "value": result.aligned_values,
        "is_interpolated": [True if i >= len(all_timestamps) or result.aligned_timestamps[i] not in all_timestamps[:len(result.aligned_timestamps)] else False
                          for i in range(len(result.aligned_timestamps))]
    })

    # 保存到CSV
    output_path = "/workspace/projects/aligned_blast_furnace_data.csv"
    df.to_csv(output_path, index=False)

    print(f"  ✓ 对齐结果已保存到: {output_path}")
    print(f"  ✓ 文件大小: {len(df)} 行")

    # 显示统计信息
    print("\n[步骤7] 数据质量报告:")
    print(f"  总数据点: {len(df)}")
    print(f"  有效值: {df['value'].notna().sum()}")
    print(f"  缺失值: {df['value'].isna().sum()}")
    print(f"  数据范围: {df['value'].min():.2f} ~ {df['value'].max():.2f}")
    print(f"  平均值: {df['value'].mean():.2f}")
    print(f"  标准差: {df['value'].std():.2f}")

    print("\n✓ 完整工作流程演示完成")


def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("GenBFKit 时间尺度对齐模板 - 使用示例集合")
    print("=" * 70)

    examples = [
        ("示例1: 时间戳标准化", example_1_timestamp_normalization),
        ("示例2: 时间序列对齐", example_2_time_series_alignment),
        ("示例3: 多源时间同步", example_3_multi_source_synchronization),
        ("示例4: 可视化对齐效果", example_4_visualize_alignment),
        ("示例5: 完整工作流程", example_5_complete_workflow),
    ]

    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    # 运行所有示例
    for name, func in examples:
        try:
            func()
        except Exception as e:
            logger.error(f"{name} 执行失败: {e}", exc_info=True)

    print("\n" + "=" * 70)
    print("所有示例执行完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
