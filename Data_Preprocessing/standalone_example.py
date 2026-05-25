"""
独立使用 Data_Preprocessing 目录的示例脚本

这个脚本演示如何在没有项目其他部分的情况下，独立使用 Data_Preprocessing 目录
"""

import pandas as pd
import numpy as np
import sys
import os

# 方法1：将 Data_Preprocessing 目录添加到 Python 路径
# 使用这个方法时，确保 Data_Preprocessing 目录与脚本在同一目录或父目录中
current_dir = os.path.dirname(os.path.abspath(__file__))
Data_Preprocessing_path = os.path.join(current_dir, "Data_Preprocessing")

if os.path.exists(Data_Preprocessing_path):
    sys.path.insert(0, Data_Preprocessing_path)
    print(f"✅ 已将 Data_Preprocessing 目录添加到 Python 路径: {Data_Preprocessing_path}")

# 方法2：如果你已经通过 pip install -e . 安装了 Data_Preprocessing 包
# 则不需要上面的代码，直接 import 即可

try:
    # 导入 Data_Preprocessing 模块
    from Data_Preprocessing.preprocessing_pipeline import PreprocessingPipeline
    from Data_Preprocessing.config import PreprocessingConfig
    print("✅ Data_Preprocessing 模块导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n请确保：")
    print("1. Data_Preprocessing 目录存在")
    print("2. 已安装依赖: pip install -r Data_Preprocessing/requirements.txt")
    print("3. Data_Preprocessing 目录已添加到 Python 路径")
    sys.exit(1)

# 生成测试数据
print("\n" + "="*60)
print("生成测试数据...")
print("="*60)

np.random.seed(42)
df = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=100, freq='H'),
    'temperature': 1500 + 50 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 5, 100),
    'pressure': 200 + 20 * np.cos(np.linspace(0, 2*np.pi, 100)) + np.random.normal(0, 2, 100),
    'flow_rate': 100 + 10 * np.sin(np.linspace(0, 3*np.pi, 100)) + np.random.normal(0, 1, 100)
})

# 注入缺失值
for col in ['temperature', 'pressure', 'flow_rate']:
    indices = np.random.choice(100, 10, replace=False)
    df.loc[indices, col] = np.nan

# 注入异常值
df.loc[50, 'temperature'] = 2000
df.loc[75, 'pressure'] = 300

print(f"✅ 测试数据生成完成")
print(f"  数据形状: {df.shape}")
print(f"  缺失值: {df.isnull().sum().sum()}")
print(f"  前5行:\n{df.head()}")

# 使用 Data_Preprocessing 进行预处理
print("\n" + "="*60)
print("使用 Data_Preprocessing 进行预处理...")
print("="*60)

config = PreprocessingConfig()
pipeline = PreprocessingPipeline(config)

steps = ["missing_values", "outlier_detection", "normalization"]
df_processed, stats = pipeline.preprocess_dataframe(df, steps=steps)

# 显示结果
print("\n" + "="*60)
print("预处理结果")
print("="*60)

print(f"✅ 预处理完成")
print(f"\n处理前后对比:")
print(f"  原始形状: {stats['original_shape']}")
print(f"  处理后形状: {stats['final_shape']}")
print(f"  缺失值: {stats['step_results']['missing_values']['final_missing_count']}")
print(f"  异常值检测: {stats['step_results']['outlier_detection']['total_outliers_detected']}")
print(f"  异常值替换: {stats['step_results']['outlier_detection']['total_outliers_replaced']}")
print(f"  归一化列数: {len(stats['step_results']['normalization']['columns_normalized'])}")

print(f"\n处理后的前5行:")
print(df_processed.head())

print("\n" + "="*60)
print("✅ Data_Preprocessing 目录独立使用测试成功！")
print("="*60)
print("\n💡 提示：")
print("  - Data_Preprocessing 目录完全独立，可以在任何项目中使用")
print("  - 查看 STANDALONE_USAGE.md 了解更多使用方法")
print("  - 查看 example_usage.py 了解更多示例")
