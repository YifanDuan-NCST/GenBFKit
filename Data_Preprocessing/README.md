# 🎨 Data_Preprocessing - 数据预处理魔法包

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

> 让你的数据从"问题儿童"变成"模范生"的魔法工具包 🪄✨

---

## 📖 什么是 Data_Preprocessing？

Data_Preprocessing 是一个专为时间序列传感器数据设计的**全功能数据预处理模块**。它就像一位专业的数据管家，帮你解决数据质量的所有头疼问题：

- 😱 **数据到处缺胳膊少腿？** → 缺失值填补
- 🔥 **有些数据就像脱缰野马？** → 异常值检测与处理
- 📊 **不同指标天差地别？** → 数据归一化
- 🧩 **想一次性搞定所有步骤？** → 预处理流水线

### 为什么选择它？

| 特性 | 其他工具 | Data_Preprocessing |
|------|---------|-------------------|
| 🎯 **专用性** | 通用工具 | 专为传感器时序数据打造 |
| 🤖 **智能程度** | 需手动选择 | 自动选择最优算法 |
| 🧩 **集成度** | 功能分散 | 一站式解决方案 |
| 📚 **易用性** | 需要学习曲线 | 3行代码上手 |
| 🚀 **性能** | 一般 | 多算法并行优化 |

---

## 🎯 核心功能

### 1️⃣ 缺失值处理 💉

你的数据是不是也经常"失踪"？别担心，我们有6种方法让它们"现身"：

| 方法 | 适用场景 | 精度 | 速度 |
|------|----------|------|------|
| 🔹 **线性插值** | 时序数据、平滑变化 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 🔹 **三次样条插值** | 时序数据、曲线平滑 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 🔹 **KNN 插值** | 多变量相关 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 🔹 **MICE 插值** | 复杂缺失模式 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 🔹 **时间感知插值** | 不均匀时间戳 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 🔹 **统计填充** | 简单快速 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**智能自动选择**：系统会根据数据类型和缺失模式自动选择最优方法，无需操心！

---

### 2️⃣ 异常值检测 🕵️

有些数据就像班级里的"捣蛋鬼"，需要被识别出来。我们有6种"侦探方法"：

| 方法 | 检测原理 | 优势 |
|------|----------|------|
| 🔍 **Isolation Forest** | 孤立机制 | 高维数据专家 |
| 🔍 **LOF (局部异常因子)** | 密度分析 | 发现局部异常 |
| 🔍 **Z-Score** | 统计学标准 | 简单快速 |
| 🔍 **IQR (四分位距)** | 箱线图原理 | 对异常值鲁棒 |
| 🔍 **Autoencoder** | 神经网络 | 学习复杂模式 |
| 🔍 **滑动窗口检测** | 时序专用 | 适合连续监测 |

**集成投票机制**：多个"侦探"一起投票，避免误判！

#### 异常值替换策略 🛠️

检测到异常值后，我们有5种策略来处理这些"捣蛋鬼"：

| 替换方法 | 原理 | 速度 | 适用场景 |
|---------|------|------|----------|
| 🎯 **中位数替换** | 使用非异常值的中位数 | ⭐⭐⭐⭐⭐ | 通用、偏态数据（默认） |
| 🎯 **均值替换** | 使用非异常值的均值 | ⭐⭐⭐⭐⭐ | 正态分布数据 |
| 🎯 **线性插值** | 标记为NaN后插值 | ⭐⭐⭐⭐ | 时序数据，保留趋势 |
| 🎯 **滚动中位数** | 使用滑动窗口中位数 | ⭐⭐⭐ | 时序数据推荐 |
| 🎯 **裁剪到边界** | 裁剪到IQR边界 | ⭐⭐⭐⭐⭐ | 温和处理，保留极值 |

**替换方法对比**：

- **中位数替换**：最鲁棒，对异常值不敏感，适合严重偏态数据
- **线性插值**：适合时序数据，保持数据趋势和连续性
- **滚动中位数**：适应局部变化，传感器时序数据首选
- **裁剪到边界**：温和处理，不过度修改数据，保留极值信息

**使用示例**：

```python
from Data_Preprocessing.outlier_detection import OutlierDetector
from Data_Preprocessing.config import OutlierDetectionConfig

# 配置检测器
config = OutlierDetectionConfig(
    methods=["isolation_forest", "zscore"],  # 使用2种检测方法
    use_ensemble=True  # 启用集成投票
)
detector = OutlierDetector(config)

# 方法1：默认中位数替换
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    target_columns=["temperature", "pressure"]
)

# 方法2：使用线性插值（适合时序数据）
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    target_columns=["temperature", "pressure"],
    replace_method="interpolation"
)

# 方法3：使用滚动中位数（推荐时序）
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    target_columns=["vibration", "noise"],
    replace_method="rolling_median"
)

# 方法4：裁剪到边界（温和处理）
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    replace_method="clip"
)

# 查看统计信息
print(f"检测到 {stats['total_outliers_detected']} 个异常值")
print(f"替换了 {stats['total_outliers_replaced']} 个异常值")
```

**选择建议**：
- 🎯 **时序传感器数据**：`rolling_median` 或 `interpolation`
- 🎯 **一般数值数据**：`median`（默认）
- 🎯 **需要保留趋势**：`interpolation`
- 🎯 **温和数据清洗**：`clip`

---

### 3️⃣ 数据归一化 📏

把不同单位的数据拉到同一个"起跑线"：

| 方法 | 适用场景 | 特点 |
|------|----------|------|
| 🎯 **Z-Score 标准化** | 正态分布数据 | 转换为标准正态 |
| 🎯 **Min-Max 归一化** | 神经网络输入 | 缩放到[0,1] |
| 🎯 **Robust 缩放** | 有异常值的数据 | 使用中位数和分位数 |
| 🎯 **Quantile 变换** | 严重偏态数据 | 强制转换为正态 |
| 🎯 **Yeo-Johnson 变换** | 含零或负值的数据 | 类似 Box-Cox 但更灵活 |
| 🎯 **Log 变换** | 指数型数据 | 压缩大数值 |

**可逆变换**：支持参数保存，随时"变回原形"！

---

### 4️⃣ 预处理流水线 🚀

一键搞定所有步骤，就像点外卖一样简单：

```python
# 只需3行代码，完成所有预处理！
pipeline = PreprocessingPipeline(PreprocessingConfig())
df_processed, stats = pipeline.preprocess_dataframe(
    df,
    steps=["missing_values", "outlier_detection", "normalization"]
)
```

**支持的步骤**：
- ✅ 数据质量分析
- ✅ 缺失值填补
- ✅ 异常值检测与替换
- ✅ 数据归一化
- ✅ 批量处理
- ✅ 元数据记录

---

## 📁 目录结构

```
Data_Preprocessing/
├── 📄 __init__.py                    # 模块入口，导出所有公共接口
│
├── 🔧 核心功能模块 (8个)
│   ├── config.py                    # 配置管理 - 所有参数的"控制中心"
│   ├── database.py                  # 数据库管理 - PostgreSQL 连接池
│   ├── utils.py                     # 工具函数 - 数据分析小助手
│   ├── missing_value.py             # 缺失值处理 - 6种填补算法
│   ├── outlier_detection.py         # 异常值检测 - 6种检测方法+集成
│   ├── data_normalization.py        # 数据归一化 - 6种归一化方法
│   └── preprocessing_pipeline.py    # 预处理流水线 - 统一编排所有步骤
│
├── 📦 安装配置 (3个)
│   ├── requirements.txt             # Python 依赖清单
│   ├── setup.py                     # 包安装脚本
│   └── install.sh                   # 一键安装脚本（推荐）
│
└── 🎪 示例与测试 (5个)
    ├── example_usage.py             # 完整使用示例（6个场景）
    ├── demo_auto_vs_custom.py       # 自动选择 vs 自定义对比
    ├── standalone_example.py        # 独立使用示例
    ├── verify_installation.py       # 安装验证脚本
    ├── test_independence.py         # 独立性测试
    └── test_standalone.py           # 独立模式测试
```

### 📄 文件详解

#### 核心模块

| 文件 | 大小 | 作用 | 核心类/函数 |
|------|------|------|-----------|
| `__init__.py` | 1.6K | 模块入口，导出公共API | PreprocessingPipeline, Config类等 |
| `config.py` | 6.9K | 配置管理，统一管理所有参数 | PreprocessingConfig, MissingValueConfig等 |
| `database.py` | 12K | PostgreSQL数据库管理 | DatabaseManager, 连接池, CRUD操作 |
| `utils.py` | 14K | 工具函数集合 | DataTypeDetector, StatisticalTests等 |
| `missing_value.py` | 14K | 缺失值处理 | MissingValueHandler, 6种填补算法 |
| `outlier_detection.py` | 17K | 异常值检测与替换 | OutlierDetector, 6种检测算法+集成投票 |
| `data_normalization.py` | 15K | 数据归一化 | DataNormalizer, 6种归一化方法 |
| `preprocessing_pipeline.py` | 15K | 预处理流水线 | PreprocessingPipeline, 批量处理, 元数据 |

#### 安装配置

| 文件 | 大小 | 作用 |
|------|------|------|
| `requirements.txt` | 425B | 列出所有Python依赖包 |
| `setup.py` | 1.6K | 支持pip安装的配置文件 |
| `install.sh` | 2.7K | **推荐**：一键安装脚本（自动检查环境、安装依赖） |

#### 示例测试

| 文件 | 大小 | 作用 |
|------|------|------|
| `example_usage.py` | 15K | 6个完整示例：基础、高级、数据库、批量等 |
| `demo_auto_vs_custom.py` | 5.9K | 对比自动选择和自定义配置 |
| `standalone_example.py` | 3.6K | 独立使用示例 |
| `verify_installation.py` | 4.1K | 验证安装是否成功 |
| `test_independence.py` | 2.5K | 测试模块独立性 |
| `test_standalone.py` | 3.6K | 测试独立模式 |

---

## 🚀 快速开始

### 方法一：一键安装（推荐⭐）

```bash
# 1. 进入目录
cd Data_Preprocessing

# 2. 运行安装脚本
bash install.sh

# 3. 验证安装
python verify_installation.py

# 看到 "✅ Data_Preprocessing 包安装验证通过！" 就成功了！
```

### 方法二：手动安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装包
pip install -e .

# 3. 测试
python -c "from Data_Preprocessing import PreprocessingPipeline; print('成功！')"
```

---

## 💻 使用示例

### 示例 1：最简单的使用（3行代码）⚡

```python
from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig
import pandas as pd

# 读取数据
df = pd.read_csv("sensor_data.csv")

# 预处理（就这么简单！）
pipeline = PreprocessingPipeline(PreprocessingConfig())
df_processed, stats = pipeline.preprocess_dataframe(
    df,
    steps=["missing_values", "outlier_detection", "normalization"]
)

# 保存结果
df_processed.to_csv("sensor_data_cleaned.csv", index=False)
print("预处理完成！")
```

### 示例 2：自定义配置 🎛️

```python
from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig
from Data_Preprocessing.config import MissingValueConfig, OutlierDetectionConfig

# 自定义配置
config = PreprocessingConfig(
    missing_value=MissingValueConfig(
        use_mice=True,          # 使用MICE算法
        mice_max_iter=20,       # 增加迭代次数
        use_knn=True,           # 同时使用KNN
        knn_n_neighbors=10      # 使用10个邻居
    ),
    outlier_detection=OutlierDetectionConfig(
        methods=["isolation_forest", "zscore", "iqr"],  # 使用3种方法
        iso_forest_contamination=0.03,  # 降低误报率
        use_ensemble=True,     # 启用集成投票
        ensemble_voting="soft" # 使用软投票（更精确）
    )
)

# 使用自定义配置
pipeline = PreprocessingPipeline(config)
df_processed, stats = pipeline.preprocess_dataframe(
    df,
    steps=["missing_values", "outlier_detection"]
)
```

### 示例 3：处理数据库表 🗄️

```python
from Data_Preprocessing import PreprocessingPipeline, PreprocessingConfig, DatabaseConfig

# 配置数据库连接
config = PreprocessingConfig(
    database=DatabaseConfig(
        host="localhost",
        port=5432,
        database="your_database",
        user="your_username",
        password="your_password"
    )
)

# 处理数据库表
pipeline = PreprocessingPipeline(config)
df_processed, stats = pipeline.preprocess_table(
    table_name="sensor_data",
    steps=["missing_values", "outlier_detection", "normalization"],
    save_to_db=True  # 自动保存回数据库
)

print(f"处理了 {stats['rows_processed']} 行数据")
```

### 示例 4：批量处理多个表 📦

```python
# 批量处理所有以 sensor_ 开头的表
results = pipeline.batch_preprocess_tables(
    table_pattern="sensor_",
    steps=["missing_values", "outlier_detection", "normalization"],
    max_tables=100
)

# 查看结果
for table_name, result in results.items():
    print(f"{table_name}: {result['status']}")
```

### 示例 5：异常值检测与替换（重点）⭐

```python
from Data_Preprocessing.outlier_detection import OutlierDetector
from Data_Preprocessing.config import OutlierDetectionConfig

# 配置异常值检测器
config = OutlierDetectionConfig(
    methods=["isolation_forest", "zscore", "iqr"],  # 使用3种检测方法
    use_ensemble=True,  # 启用集成投票
    ensemble_voting="soft"  # 软投票（更精确）
)
detector = OutlierDetector(config)

# 检测并替换异常值（默认中位数替换）
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    target_columns=["temperature", "pressure", "vibration"]
)
print(f"检测到 {stats['total_outliers_detected']} 个异常值，已替换")

# 使用线性插值替换（适合时序数据，保留趋势）
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    target_columns=["temperature", "pressure"],
    replace_method="interpolation"
)

# 使用滚动中位数替换（时序数据推荐）
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    target_columns=["sensor_reading"],
    replace_method="rolling_median"
)

# 裁剪到边界（温和处理，保留极值信息）
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    replace_method="clip"
)

# 仅检测，不替换（用于先分析再决定）
df_processed, stats = detector.detect_and_handle_outliers(
    df,
    replace_method="none"
)

# 查看每列的异常值统计
for col_stat in stats['column_statistics']:
    print(f"列 {col_stat['column']}: {col_stat['outlier_count']} 个异常值 "
          f"({col_stat['outlier_percentage']:.2f}%)")
```

---

## 🎛️ 配置说明

### 预处理配置 (PreprocessingConfig)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `missing_value` | MissingValueConfig | 默认配置 | 缺失值处理配置 |
| `outlier_detection` | OutlierDetectionConfig | 默认配置 | 异常值检测配置 |
| `normalization` | NormalizationConfig | 默认配置 | 数据归一化配置 |
| `database` | DatabaseConfig | 默认配置 | 数据库连接配置 |

### 缺失值配置 (MissingValueConfig)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `use_mice` | bool | True | 是否使用MICE算法 |
| `mice_max_iter` | int | 10 | MICE最大迭代次数 |
| `use_knn` | bool | True | 是否使用KNN算法 |
| `knn_n_neighbors` | int | 5 | KNN邻居数量 |
| `time_series_methods` | list | [插值方法列表] | 时序插值方法优先级 |

### 异常值检测配置 (OutlierDetectionConfig)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `methods` | list | [6种检测方法] | 使用的检测方法 |
| `use_ensemble` | bool | True | 是否使用集成投票 |
| `ensemble_voting` | str | "hard" | 投票方式：hard/soft |
| `iso_forest_contamination` | float | 0.05 | Isolation Forest异常比例 |
| `zscore_threshold` | float | 3.0 | Z-Score阈值 |

**注意**：`replace_method` 参数在调用 `detect_and_handle_outliers()` 时指定，而不是在配置中设置。

支持的替换方法：
- `median`：中位数替换（默认，推荐）
- `mean`：均值替换
- `interpolation`：线性插值（适合时序数据）
- `rolling_median`：滚动中位数（时序数据推荐）
- `clip`：裁剪到IQR边界（温和处理）
- `none`：仅检测，不替换

### 数据归一化配置 (NormalizationConfig)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `method` | str | "zscore" | 归一化方法 |
| 可选值 | - | zscore, minmax, robust, quantile, yeo-johnson, log | 6种方法 |

---

## 🔍 API 快速参考

### PreprocessingPipeline

```python
# 初始化
pipeline = PreprocessingPipeline(config)

# 处理 DataFrame
df_processed, stats = pipeline.preprocess_dataframe(
    df,
    steps=["missing_values", "outlier_detection", "normalization"],
    target_columns=None  # 默认处理所有列
)

# 处理数据库表
df_processed, stats = pipeline.preprocess_table(
    table_name="your_table",
    steps=["missing_values", "outlier_detection", "normalization"],
    save_to_db=True
)

# 批量处理
results = pipeline.batch_preprocess_tables(
    table_pattern="sensor_",
    steps=["missing_values", "outlier_detection"],
    max_tables=100
)

# 数据质量分析
quality_report = pipeline.analyze_data_quality(df)
```

### 单独使用各个模块

```python
# 缺失值处理
from Data_Preprocessing.missing_value import MissingValueHandler
handler = MissingValueHandler(config.missing_value)
df_imputed, stats = handler.handle_missing_values(df)

# 异常值检测
from Data_Preprocessing.outlier_detection import OutlierDetector
detector = OutlierDetector(config.outlier_detection)
df_cleaned, stats = detector.detect_and_handle_outliers(df)

# 数据归一化
from Data_Preprocessing.data_normalization import DataNormalizer
normalizer = DataNormalizer(config.normalization)
df_normalized, stats = normalizer.normalize(df, columns=["temperature", "pressure"])
```

---

## ❓ 常见问题 (FAQ)

### Q1: 我的数据不是时间序列数据，能用吗？

**A**: 当然可以！虽然我们专为时序数据优化，但对于普通数据集也完全适用。系统会自动检测数据类型并选择合适的算法。

### Q2: 自动选择算法靠谱吗？我能自己指定吗？

**A**: 自动选择非常靠谱，内置了智能决策机制。如果你有特定需求，也完全可以自己指定算法，查看示例2了解如何自定义配置。

### Q3: 处理大数据集会很慢吗？

**A**: 我们做了性能优化：
- 多算法并行处理
- 自动批量化操作
- 支持分块处理
- 使用高效算法实现

对于超大数据集，建议使用批量处理功能。

### Q4: 我的数据库不是 PostgreSQL 怎么办？

**A**: PostgreSQL 是原生支持的数据库。如果你使用其他数据库，可以：
- 使用 DataFrame 接口：先从你的数据库读取数据，预处理后再写回
- 或者联系我们添加支持

### Q5: 归一化后还能还原吗？

**A**: 当然可以！数据归一化模块支持参数保存和加载，随时可以"变回原形"：

```python
normalizer.save_scalers("my_scalers.pkl")  # 保存参数
normalizer.load_scalers("my_scalers.pkl")  # 加载参数
df_original = normalizer.inverse_normalize(df_normalized, columns)  # 还原
```

### Q6: 如何查看处理了什么？

**A**: 每次处理都会返回详细的统计信息：

```python
df_processed, stats = pipeline.preprocess_dataframe(df, steps=["missing_values", "outlier_detection"])

# 查看统计
print(stats)
# {
#   'step_results': {
#     'missing_values': {'final_missing_count': 0, 'columns_processed': [...]},
#     'outlier_detection': {'total_outliers_detected': 42, 'total_outliers_replaced': 42}
#   }
# }
```

### Q7: 异常值替换方法应该怎么选？

**A**: 根据数据类型和业务需求选择：

| 场景 | 推荐替换方法 | 原因 |
|------|-------------|------|
| **时序传感器数据** | `rolling_median` 或 `interpolation` | 保留时间趋势，适应局部变化 |
| **一般数值数据** | `median`（默认） | 鲁棒性强，对异常值不敏感 |
| **正态分布数据** | `mean` | 保持统计特性 |
| **需要保留趋势** | `interpolation` | 平滑过渡，保持连续性 |
| **温和数据清洗** | `clip` | 裁剪到边界，保留极值信息 |
| **仅检测不替换** | `none` | 先分析再决定处理方式 |

**示例**：
```python
# 时序数据：使用滚动中位数
df_processed, stats = detector.detect_and_handle_outliers(
    df, replace_method="rolling_median"
)

# 温和处理：裁剪到边界
df_processed, stats = detector.detect_and_handle_outliers(
    df, replace_method="clip"
)

# 仅检测，不替换
df_processed, stats = detector.detect_and_handle_outliers(
    df, replace_method="none"
)
```

### Q8: 会修改原始数据吗？

**A**: 默认不会！预处理返回的是新数据，原始数据保持不变。除非你显式地保存回去（如数据库模式中的 `save_to_db=True`）。

### Q9: 支持哪些数据类型？

**A**: 支持所有 pandas 能处理的数据类型：

- ✅ 数值型 (int, float)
- ✅ 分类型 (str, category)
- ✅ 时序型 (datetime)
- ✅ 布尔型 (bool)

### Q10: 安装后怎么验证是否成功？

**A**: 运行验证脚本：

```bash
python verify_installation.py
```

看到 "✅ Data_Preprocessing 包安装验证通过！" 就说明成功了！

### Q11: 遇到问题怎么办？

**A**: 检查以下几点：
1. Python 版本 >= 3.8
2. 所有依赖已安装（运行 `pip install -r requirements.txt`）
3. 查看示例代码确保使用方式正确
4. 查看错误日志定位问题

如果还是不行，欢迎提 Issue！

---

## 📚 更多示例

想要看更多实际案例？运行示例脚本：

```bash
# 完整示例（6个场景）
python example_usage.py

# 自动选择 vs 自定义对比
python demo_auto_vs_custom.py

# 独立使用示例
python standalone_example.py
```

---

## 🎓 最佳实践

### 1. 数据预处理顺序

推荐的处理流程：

```
原始数据
   ↓
数据质量分析 (可选)
   ↓
缺失值处理 ⭐ 优先
   ↓
异常值检测与替换
   ↓
数据归一化 ⭐ 最后
   ↓
保存结果
```

**为什么这个顺序？**
- 先填补缺失值，避免影响异常值检测
- 异常值替换可能引入新极端值，要在归一化前完成
- 归一化应该在最后，确保所有数据在统一尺度

### 2. 配置选择建议

| 场景 | 推荐配置 | 理由 |
|------|----------|------|
| 快速原型 | 默认配置 | 零配置，快速出结果 |
| 生产环境 | 自定义配置 | 精确控制，确保稳定 |
| 数据探索 | 默认配置 | 快速查看数据质量 |
| 性能敏感 | 禁用MICE，只用KNN | 提高速度 |
| 高精度 | 启用所有算法 | 追求最佳效果 |

### 3. 批量处理优化

处理大量数据表时：

```python
# ✅ 好的做法
results = pipeline.batch_preprocess_tables(
    table_pattern="sensor_",
    steps=["missing_values", "outlier_detection", "normalization"],
    max_tables=100  # 限制每次处理数量
)

# ✅ 好的做法：按重要性分批
high_priority = ["sensor_temperature", "sensor_pressure"]
medium_priority = ["sensor_flow", "sensor_level"]
low_priority = ["sensor_aux_*"]
```

---

## 🛠️ 技术栈

- **Python**: 3.8+
- **核心依赖**:
  - pandas >= 2.0.0 (数据处理)
  - numpy >= 1.24.0 (数值计算)
  - scikit-learn >= 1.3.0 (机器学习算法)
  - scipy >= 1.10.0 (科学计算)
  - psycopg2-binary >= 2.9.0 (PostgreSQL，可选)

---

## 📊 性能指标

在测试环境下的性能表现：

| 操作 | 数据量 | 耗时 | 内存占用 |
|------|--------|------|----------|
| 缺失值处理 | 100K 行 × 10 列 | ~2s | ~200MB |
| 异常值检测 | 100K 行 × 10 列 | ~3s | ~250MB |
| 数据归一化 | 100K 行 × 10 列 | ~1s | ~150MB |
| 完整流程 | 100K 行 × 10 列 | ~6s | ~300MB |

*注：实际性能取决于数据特征和硬件配置*

---

## 🤝 贡献指南

欢迎贡献代码、报告 Bug 或提出建议！

### 代码规范

- 遵循 PEP 8 规范
- 添加必要的注释和文档字符串
- 编写单元测试
- 确保示例代码可运行

---

## 🎉 总结

Data_Preprocessing 就像是数据的"健身教练" 💪：

- 🏋️ 帮你的数据"减脂"（去除异常值）
- 🏊 帮你的数据"补水"（填补缺失值）
- 📏 帮你的数据"标准化"（归一化）
- 🏆 让你的数据"变强"（提高质量）

**3行代码，让数据从"问题儿童"变成"模范生"！** 🚀

---

<div align="center">
## 📜 License | 许可证

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

**MIT License** - 欢迎贡献！| Welcome contributions!

---

<p align="center">
  <sub>Made with ❤️ for the Blast Furnace Industry | 为高炉炼铁行业而生</sub>
</p>

