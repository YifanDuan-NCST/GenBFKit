#!/usr/bin/env python3
"""
验证 Data_Preprocessing 包的安装和功能
"""

import sys
import pandas as pd
import numpy as np

print("="*60)
print("Data_Preprocessing 包安装验证")
print("="*60)
print()

# 测试 1: 导入测试
print("测试 1: 导入模块...")
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
        NormalizationConfig,
        DatabaseConfig
    )
    print("✅ 所有模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("\n请运行安装脚本:")
    print("  bash install.sh")
    print("\n或手动安装:")
    print("  pip install -e .")
    sys.exit(1)

# 测试 2: 配置加载
print("\n测试 2: 配置加载...")
try:
    config = PreprocessingConfig()
    print("✅ 配置加载成功")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    sys.exit(1)

# 测试 3: 数据处理
print("\n测试 3: 数据预处理...")
try:
    # 生成测试数据
    np.random.seed(42)
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

    print("✅ 数据预处理成功")
    print(f"  原始形状: {df.shape}")
    print(f"  处理后形状: {df_processed.shape}")
    print(f"  缺失值: {stats['step_results']['missing_values']['final_missing_count']}")
    print(f"  异常值: {stats['step_results']['outlier_detection']['total_outliers_detected']}")
except Exception as e:
    print(f"❌ 数据预处理失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 4: 自定义配置
print("\n测试 4: 自定义配置...")
try:
    custom_config = PreprocessingConfig(
        missing_value=MissingValueConfig(
            use_mice=True,
            mice_max_iter=5
        ),
        outlier_detection=OutlierDetectionConfig(
            methods=["zscore"],
            zscore_threshold=2.5
        )
    )

    pipeline = PreprocessingPipeline(custom_config)
    df_processed, stats = pipeline.preprocess_dataframe(
        df,
        steps=["missing_values", "outlier_detection"]
    )

    print("✅ 自定义配置测试成功")
except Exception as e:
    print(f"❌ 自定义配置测试失败: {e}")
    sys.exit(1)

# 测试 5: 归一化
print("\n测试 5: 数据归一化...")
try:
    from Data_Preprocessing import DataNormalizer, NormalizationConfig

    norm_config = NormalizationConfig(method="zscore")
    normalizer = DataNormalizer(norm_config)

    df_norm, stats = normalizer.normalize(df, columns=["value"])

    print("✅ 数据归一化成功")
    print(f"  归一化方法: {stats['method']}")
    print(f"  归一化列数: {len(stats['columns_normalized'])}")
except Exception as e:
    print(f"❌ 数据归一化失败: {e}")
    sys.exit(1)

# 所有测试通过
print("\n" + "="*60)
print("✅ Data_Preprocessing 包安装验证通过！")
print("="*60)
print()
print("所有功能正常，可以开始使用了！")
print()
print("使用示例:")
print()
print("  from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig")
print()
print("  # 读取数据")
print("  import pandas as pd")
print("  df = pd.read_csv('data.csv')")
print()
print("  # 预处理")
print("  config = PreprocessingConfig()")
print("  pipeline = PreprocessingPipeline(config)")
print("  df_processed, stats = pipeline.preprocess_dataframe(")
print("      df,")
print("      steps=['missing_values', 'outlier_detection', 'normalization']")
print("  )")
print()
print("  # 保存结果")
print("  df_processed.to_csv('data_cleaned.csv', index=False)")
print()
print("查看更多示例:")
print("  python example_usage.py")
print()
print("查看文档:")
print("  cat README.md")
print("  cat USAGE_GUIDE.md")
print()
