#!/usr/bin/env python3
"""
测试 Data_Preprocessing 目录的独立性
验证：只使用 Data_Preprocessing 目录的文件是否能独立运行
"""

import sys
import os

# 模拟只下载 Data_Preprocessing 目录的场景
# 将 Data_Preprocessing 目录添加到 Python 路径
Data_Preprocessing_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, Data_Preprocessing_path)

# 测试导入
try:
    from Data_Preprocessing import (
        PreprocessingPipeline,
        PreprocessingConfig,
        MissingValueHandler,
        OutlierDetector,
        DataNormalizer,
        DatabaseManager,
        MissingValueConfig,
        OutlierDetectionConfig,
        NormalizationConfig
    )
    print("✅ 所有模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

# 测试配置加载
try:
    config = PreprocessingConfig()
    print("✅ 配置加载成功")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    sys.exit(1)

# 测试数据处理（不依赖数据库）
try:
    import pandas as pd
    import numpy as np

    # 生成测试数据
    df = pd.DataFrame({
        'value': [1, 2, np.nan, 4, 5, 100, 7, 8, 9, 10]
    })

    # 创建流水线
    pipeline = PreprocessingPipeline(config)

    # 处理数据
    df_processed, stats = pipeline.preprocess_dataframe(
        df,
        steps=["missing_values", "outlier_detection", "normalization"]
    )

    print("✅ 数据处理成功")
    print(f"  原始形状: {df.shape}")
    print(f"  处理后形状: {df_processed.shape}")
    print(f"  缺失值: {stats['step_results']['missing_values']['final_missing_count']}")
    print(f"  异常值: {stats['step_results']['outlier_detection']['total_outliers_detected']}")

except Exception as e:
    print(f"❌ 数据处理失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ Data_Preprocessing 目录完全独立，可以单独使用！")
print("="*60)
print("\n使用方法：")
print("1. 下载 Data_Preprocessing 目录")
print("2. 安装依赖: pip install -r Data_Preprocessing/requirements.txt")
print("3. 使用代码:")
print("""
   from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig

   config = PreprocessingConfig()
   pipeline = PreprocessingPipeline(config)
   df_processed, stats = pipeline.preprocess_dataframe(df, steps=["missing_values", "outlier_detection", "normalization"])
""")
