"""
演示：自动选择 vs 自定义方法
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/workspace/projects')

from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig
from Data_Preprocessing import MissingValueHandler, MissingValueConfig
from Data_Preprocessing import OutlierDetector, OutlierDetectionConfig
from Data_Preprocessing import DataNormalizer, NormalizationConfig

def generate_test_data():
    """生成测试数据"""
    timestamps = [datetime(2024, 1, 1) + timedelta(minutes=i) for i in range(200)]
    np.random.seed(42)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'temperature': 1500 + 50 * np.sin(np.linspace(0, 4*np.pi, 200)) + np.random.normal(0, 5, 200),
        'pressure': 200 + 20 * np.cos(np.linspace(0, 2*np.pi, 200)) + np.random.normal(0, 2, 200)
    })

    # 注入缺失值
    for col in ['temperature', 'pressure']:
        indices = np.random.choice(200, 20, replace=False)
        df.loc[indices, col] = np.nan

    # 注入异常值
    df.loc[50, 'temperature'] = 2000
    df.loc[100, 'pressure'] = 300

    return df

print("=" * 70)
print("GenBFKit 数据预处理模块 - 自动选择 vs 自定义方法演示")
print("=" * 70)
print()

# 生成测试数据
df = generate_test_data()
print(f"测试数据:")
print(f"  形状: {df.shape}")
print(f"  缺失值: {df.isnull().sum().sum()}")
print()

# ============================================================================
# 模式1：自动选择（默认配置）
# ============================================================================
print("-" * 70)
print("模式1：自动选择（使用默认配置）")
print("-" * 70)
print()

config_auto = PreprocessingConfig()
pipeline_auto = PreprocessingPipeline(config_auto)

df_auto, stats_auto = pipeline_auto.preprocess_dataframe(
    df,
    steps=["missing_values", "outlier_detection", "normalization"]
)

print("✓ 处理完成")
print()
print("统计结果:")
print(f"  原始形状: {stats_auto['original_shape']}")
print(f"  最终形状: {stats_auto['final_shape']}")

# 显示使用的方法
print()
print("自动选择的方法:")
for step, step_stats in stats_auto.get('step_results', {}).items():
    print(f"  {step}:")
    if 'imputation_methods_used' in step_stats:
        print(f"    缺失值填补方法: {step_stats['imputation_methods_used']}")
    if 'total_outliers_detected' in step_stats:
        print(f"    异常值检测方法: ensemble (isolation_forest + lof + zscore + iqr)")
        print(f"    异常值检测数量: {step_stats['total_outliers_detected']}")
    if 'method' in step_stats:
        print(f"    归一化方法: {step_stats['method']}")

print()

# ============================================================================
# 模式2：自定义配置
# ============================================================================
print("-" * 70)
print("模式2：自定义配置（手动指定方法）")
print("-" * 70)
print()

print("自定义配置:")
config_custom = PreprocessingConfig(
    missing_value=MissingValueConfig(
        # 禁用MICE（提高速度）
        use_mice=False,
        # 只使用KNN
        use_knn=True,
        knn_n_neighbors=3,
        # 时序插值只使用线性插值
        time_series_methods=["linear_interpolation"]
    ),
    outlier_detection=OutlierDetectionConfig(
        # 只使用Z-Score和IQR（快速方法）
        methods=["zscore", "iqr"],
        # 降低Z-Score阈值（更宽松）
        zscore_threshold=2.5,
        # 禁用集成
        use_ensemble=False
    ),
    normalization=NormalizationConfig(method="robust")  # 使用鲁棒缩放
)

print("  缺失值处理:")
print("    - 禁用MICE")
print("    - 使用KNN（k=3）")
print("    - 时序插值：仅线性插值")
print()
print("  异常值检测:")
print("    - 方法：Z-Score + IQR")
print("    - Z-Score阈值：2.5")
print("    - 禁用集成投票")
print()
print("  数据归一化:")
print("    - 方法：Robust缩放")
print()

pipeline_custom = PreprocessingPipeline(config_custom)
df_custom, stats_custom = pipeline_custom.preprocess_dataframe(
    df,
    steps=["missing_values", "outlier_detection", "normalization"]
)

print("✓ 处理完成")
print()
print("统计结果:")
print(f"  原始形状: {stats_custom['original_shape']}")
print(f"  最终形状: {stats_custom['final_shape']}")

# 显示使用的方法
print()
print("自定义配置使用的方法:")
for step, step_stats in stats_custom.get('step_results', {}).items():
    print(f"  {step}:")
    if 'imputation_methods_used' in step_stats:
        print(f"    缺失值填补方法: {step_stats['imputation_methods_used']}")
    if 'total_outliers_detected' in step_stats:
        print(f"    异常值检测方法: zscore + iqr")
        print(f"    异常值检测数量: {step_stats['total_outliers_detected']}")
    if 'method' in step_stats:
        print(f"    归一化方法: {step_stats['method']}")

print()

# ============================================================================
# 对比总结
# ============================================================================
print("=" * 70)
print("对比总结")
print("=" * 70)
print()

print("自动选择模式:")
print("  ✓ 无需配置，开箱即用")
print("  ✓ 自动选择最优算法")
print("  ✓ 集成投票，降低误报")
print("  ✓ 适合快速开发")
print()

print("自定义配置模式:")
print("  ✓ 完全控制算法选择")
print("  ✓ 可根据业务需求调优")
print("  ✓ 可优化性能（速度/精度平衡）")
print("  ✓ 适合生产环境")
print()

print("建议:")
print("  • 开发阶段：使用自动选择，快速迭代")
print("  • 测试阶段：尝试不同配置，对比效果")
print("  • 生产阶段：使用经过验证的自定义配置")
print()

print("=" * 70)
print("演示完成")
print("=" * 70)
print()
