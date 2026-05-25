"""
测试异常检测功能
"""
from time_scale_alignment_template import (
    TimeScaleAlignmentTemplate,
    TimeAlignmentConfig,
    InterpolationMethod
)
from datetime import datetime, timezone, timedelta
import numpy as np

# 创建配置，启用异常检测
config = TimeAlignmentConfig(
    target_frequency="1S",
    default_interpolation=InterpolationMethod.LINEAR,
    enable_outlier_detection=True,
    outlier_threshold_sigma=3.0  # 3σ原则
)

# 创建模板实例
tsat = TimeScaleAlignmentTemplate(config)

print("=" * 60)
print("异常检测功能测试")
print("=" * 60)

# 生成测试数据（包含异常值）
timestamps = [
    datetime.now(timezone.utc) + timedelta(seconds=i)
    for i in range(20)
]

# 正常值范围：1400-1600
values = [1500 + np.random.normal(0, 50) for _ in range(20)]

# 插入几个异常值
values[5] = 2500.0  # 明显异常
values[10] = 500.0   # 明显异常
values[15] = 1800.0  # 边界异常

print(f"\n原始数据:")
print(f"  - 数据点数: {len(timestamps)}")
print(f"  - 均值: {np.mean(values):.2f}")
print(f"  - 标准差: {np.std(values):.2f}")
print(f"  - 最小值: {min(values):.2f}")
print(f"  - 最大值: {max(values):.2f}")

print(f"\n已插入异常值:")
print(f"  - 值[5] = {values[5]} (异常)")
print(f"  - 值[10] = {values[10]} (异常)")
print(f"  - 值[15] = {values[15]} (可能异常)")

# 执行对齐
result = tsat.align_time_series(
    timestamps,
    values,
    table_name="test_outlier_detection"
)

print(f"\n对齐结果:")
print(f"  - 对齐时间点数: {len(result.aligned_timestamps)}")
print(f"  - 插值数量: {result.interpolated_count}")
print(f"  - 缺失数量: {result.missing_count}")
print(f"  - 异常数量: {result.outlier_count}")

if result.outlier_count > 0:
    print(f"\n检测到的异常值索引: {result.outlier_indices}")
    print(f"异常值详情:")
    for idx in result.outlier_indices:
        if idx < len(result.aligned_values):
            value = result.aligned_values[idx]
            ts = result.aligned_timestamps[idx]
            print(f"  - 索引 {idx}: 时间={ts.strftime('%H:%M:%S')}, 值={value:.2f}")

# 重新计算均值和标准差（排除None值）
valid_values = [v for v in result.aligned_values if v is not None]
print(f"\n对齐后统计:")
print(f"  - 有效值数量: {len(valid_values)}")
print(f"  - 均值: {np.mean(valid_values):.2f}")
print(f"  - 标准差: {np.std(valid_values):.2f}")

print("\n" + "=" * 60)
print("异常检测功能测试完成！")
print("=" * 60)
