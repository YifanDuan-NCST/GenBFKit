"""
独立使用 Data_Preprocessing 目录的测试脚本
直接从 Data_Preprocessing 目录导入模块，不通过包方式
"""

import pandas as pd
import numpy as np
import sys
import os

# 将 Data_Preprocessing 目录添加到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir 应该是 Data_Preprocessing 目录本身，因为脚本在 Data_Preprocessing 目录下
Data_Preprocessing_path = current_dir

if os.path.exists(Data_Preprocessing_path):
    sys.path.insert(0, Data_Preprocessing_path)
    print(f"✅ 已将 Data_Preprocessing 目录添加到 Python 路径: {Data_Preprocessing_path}\n")
else:
    print(f"❌ Data_Preprocessing 目录不存在: {Data_Preprocessing_path}")
    sys.exit(1)

# 直接导入模块（不使用包方式）
try:
    import preprocessing_pipeline
    import config
    print("✅ 模块导入成功\n")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 生成测试数据
print("="*60)
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

# 使用预处理流水线
print("\n" + "="*60)
print("使用 Data_Preprocessing 进行预处理...")
print("="*60)

# 创建配置
cfg = config.PreprocessingConfig()

# 创建流水线
pipeline = preprocessing_pipeline.PreprocessingPipeline(cfg)

# 预处理
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
print(f"  归一化列数: {len(stats['step_results']['normalization']['columns_normalized'])}")

print(f"\n处理后的前5行:")
print(df_processed.head())

print("\n" + "="*60)
print("✅ Data_Preprocessing 目录独立使用测试成功！")
print("="*60)

print("\n💡 使用方法：")
print("""
# 方法1：直接导入模块（无需安装）
import sys
sys.path.append('Data_Preprocessing')
import preprocessing_pipeline as pp
import config as cfg

pipeline = pp.PreprocessingPipeline(cfg.PreprocessingConfig())
df_processed, stats = pipeline.preprocess_dataframe(df, steps=["missing_values", "outlier_detection"])

# 方法2：通过 pip 安装为包（推荐）
cd Data_Preprocessing
pip install -e .

from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig
pipeline = PreprocessingPipeline(PreprocessingConfig())
df_processed, stats = pipeline.preprocess_dataframe(df, steps=["missing_values", "outlier_detection"])
""")
