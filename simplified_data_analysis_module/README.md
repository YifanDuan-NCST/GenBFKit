# 🚀 GenBFKit 简易数据分析模块

> 让数据分析变得像喝咖啡一样简单 ☕

---

## 📖 简介

欢迎来到 **GenBFKit 简易数据分析模块**！这里是你的数据分析游乐场 🎡，专为准工业数据打造的智能分析工具包。基于预处理后的数据集，本模块提供三大核心分析功能：

### 🎯 三大核心功能

1. **📊 统计指标分析** - 5大指标秒懂数据特征
2. **🔗 相关性分析** - 看透参数间的"爱恨情仇"
3. **🎯 SHAP可解释性分析** - 让XGBoost模型"开口说话"

---

## 🌟 功能亮点

### 1️⃣ 统计指标分析 `StatisticalAnalyzer`

**别让数据藏着掖着，5个指标让它原形毕露！**

| 指标 | 英文名 | 作用 | 适用场景 |
|------|--------|------|----------|
| 📈 均值 | Mean | 数据的中心位置 | 了解整体水平 |
| 📏 标准差 | Standard Deviation | 数据的离散程度 | 判断数据波动大小 |
| 🎯 变异系数 | Coefficient of Variation | 相对变异程度 | 比较不同参数的稳定性 |
| ↔️ 偏度 | Skewness | 分布不对称性 | 识别左偏/右偏/对称 |
| 🔺 峰度 | Kurtosis | 分布尖锐程度 | 判断是否集中或分散 |

**特色功能：**
- ✨ 自动生成详细分析报告
- 🎨 4种精美可视化图表
- 📋 智能解读指标含义
- 💾 一键导出CSV格式结果

**使用示例：**
```python
from simplified_data_analysis_module.statistical_analysis import StatisticalAnalyzer

# 加载数据
data = pd.read_excel('your_data.xlsx')

# 创建分析器
analyzer = StatisticalAnalyzer(data)

# 计算所有指标
metrics = analyzer.calculate_all_metrics()
print(metrics)

# 生成报告
report = analyzer.generate_report(output_path='statistical_report.txt')

# 绘制可视化图表
analyzer.plot_metrics(save_folder='statistical_plots')

# 导出结果
analyzer.export_metrics(output_path='statistical_metrics.csv')
```

---

### 2️⃣ 相关性分析 `CorrelationAnalyzer`

**参数之间谁跟谁好？一张图全搞定！**

**支持的3种相关系数方法：**

- 🧮 **Pearson** - 线性相关性（最常用）
- 📊 **Spearman** - 单调相关性（非线性也行）
- 🎲 **Kendall** - 秩相关性（小样本友好）

**可视化特性：**
- 🔵 **节点大小** → 与目标变量的相关性强度
- 🎨 **节点颜色** → 相关性方向（红正蓝负）
- 📏 **连线粗细** → 参数间的相关性强度
- 🌈 **连线颜色** → 相关性方向
- 📐 **线型样式** → 显著性（实线=显著，虚线=不显著）

**5种颜色方案 + 5种形状标记 = 25种炫酷组合！** 🎨

**使用示例：**
```python
from simplified_data_analysis_module.correlation_analysis import CorrelationAnalyzer

# 加载数据
data = pd.read_excel('your_data.xlsx')
X = data.drop(columns=['target'])
y = data['target']

# 创建分析器
analyzer = CorrelationAnalyzer(data, target_column='target')

# 设置方法（可选）
analyzer.set_method('pearson')  # 或 'spearman', 'kendall'

# 设置可视化样式（可选）
analyzer.set_visualization_style(scheme_index=1, style_index=1)

# 计算相关性
results = analyzer.calculate_correlation()

# 绘制相关性网络图
analyzer.plot_correlation_network(save_path='correlation_network.pdf')

# 获取前10对相关性最强的参数
top_corr = analyzer.get_top_correlations(n=10)
print(top_corr)

# 导出相关性矩阵
analyzer.export_correlation_matrix(output_path='correlation_matrix.csv')
```

---

### 3️⃣ SHAP可解释性分析 `SHAPAnalyzer`

**XGBoost的"内心戏"，SHAP帮你全扒出来！** 🎭

**核心功能：**
- 🤖 **自动超参数优化** - GridSearchCV自动找最佳参数
- 📊 **模型性能评估** - R²、RMSE、MAE三大指标
- 🎯 **SHAP值计算** - 主效应 + 交互效应全都有
- 📈 **丰富的可视化** - 回归拟合图、特征重要性图、依赖图
- 💎 **交互效应分析** - 揭示参数间的复杂关系

**生成图表类型：**
1. 📉 **回归拟合图** - 看预测准不准
2. 📊 **特征重要性总览图** - 蜂群图 + 条形图组合
3. 📈 **SHAP依赖图** - 每个特征一个图
4. 🔗 **交互效应图** - 参数间关系可视化

**使用示例：**
```python
from simplified_data_analysis_module.shap_analysis import SHAPAnalyzer

# 加载数据
data = pd.read_excel('your_data.xlsx')
X = data.drop(columns=['target'])
y = data['target']

# 创建分析器
analyzer = SHAPAnalyzer(X, y, test_size=0.3, random_state=42)

# 运行完整分析（一键搞定！）
analyzer.run_full_analysis()

# 或者分步执行
# analyzer.preprocess_data()
# analyzer.train_model()
# analyzer.evaluate_model()
# analyzer.calculate_shap_values()
# analyzer.plot_regression_fit()
# analyzer.plot_feature_importance()
# analyzer.plot_dependence_plots()
# analyzer.export_feature_importance()
```

---

## 🎲 虚拟数据生成器

**没有真实数据？没问题！我们帮你造！** 🏭

**MockDataGenerator** 提供3种数据生成方式：

1. **高炉工况模拟数据** - 模拟真实高炉运行参数
2. **特定模式测试数据** - 包含正态、偏态、周期性等多种分布
3. **简单测试数据** - 快速生成用于基础测试

**使用示例：**
```python
from simplified_data_analysis_module.data_generator import MockDataGenerator

# 创建生成器
generator = MockDataGenerator(n_samples=1000, random_state=42)

# 生成高炉工况数据
bf_data = generator.generate_blast_furnace_data()

# 生成特定模式数据
pattern_data = generator.generate_synthetic_data_with_patterns()

# 生成简单测试数据
simple_data = generator.generate_simple_test_data(n_features=15)

# 保存到Excel
generator.save_to_excel(data, filename='test_data.xlsx')
```

---

## 📦 项目结构

```
simplified_data_analysis_module/
├── 📊 statistical_analysis/        # 统计指标分析
│   ├── __init__.py
│   └── statistical_analyzer.py
├── 🔗 correlation_analysis/        # 相关性分析
│   ├── __init__.py
│   └── correlation_analyzer.py
├── 🎯 shap_analysis/               # SHAP分析
│   ├── __init__.py
│   └── shap_analyzer.py
├── 🎲 data_generator/              # 虚拟数据生成
│   ├── __init__.py
│   └── mock_data_generator.py
└── 📖 README.md                    # 本文档
```

---

## 🚀 快速开始

### 安装依赖

```bash
pip install pandas numpy matplotlib seaborn scipy scikit-learn xgboost shap networkx openpyxl
```

### 完整示例

```python
import pandas as pd
from simplified_data_analysis_module.data_generator import MockDataGenerator
from simplified_data_analysis_module.statistical_analysis import StatisticalAnalyzer
from simplified_data_analysis_module.correlation_analysis import CorrelationAnalyzer
from simplified_data_analysis_module.shap_analysis import SHAPAnalyzer

# 步骤1: 生成测试数据
print("🎲 生成测试数据...")
generator = MockDataGenerator(n_samples=1000, random_state=42)
data = generator.generate_blast_furnace_data()

# 步骤2: 统计指标分析
print("\n📊 统计指标分析...")
stat_analyzer = StatisticalAnalyzer(data)
metrics = stat_analyzer.calculate_all_metrics()
stat_analyzer.generate_report('statistical_report.txt')
stat_analyzer.plot_metrics('statistical_plots')
stat_analyzer.export_metrics('statistical_metrics.csv')

# 步骤3: 相关性分析
print("\n🔗 相关性分析...")
X = data.drop(columns=['铁水温度'])
y = data['铁水温度']
corr_analyzer = CorrelationAnalyzer(data, target_column='铁水温度')
corr_analyzer.set_method('pearson')
corr_analyzer.calculate_correlation()
corr_analyzer.plot_correlation_network('correlation_network.pdf')
corr_analyzer.export_correlation_matrix('correlation_matrix.csv')

# 步骤4: SHAP分析
print("\n🎯 SHAP分析...")
shap_analyzer = SHAPAnalyzer(X, y, test_size=0.3, random_state=42)
shap_analyzer.run_full_analysis()

print("\n✅ 所有分析完成！")
```

---

## 🎨 使用技巧

### 💡 统计指标分析
- **变异系数 > 30%** → 参数波动较大，需要关注 ⚠️
- **偏度 > 0.5** → 右偏分布，可能有异常高值 📈
- **峰度 > 3** → 尖峰分布，数据集中在均值附近 🔺

### 🔗 相关性分析
- **P值 < 0.05** → 相关性显著 ✅
- **|相关系数| > 0.7** → 强相关 🔥
- **|相关系数| > 0.4 且 < 0.7** → 中等相关 🌤️
- **|相关系数| < 0.4** → 弱相关 ❄️

### 🎯 SHAP分析
- **SHAP值 > 0** → 对预测结果有正向贡献 📈
- **SHAP值 < 0** → 对预测结果有负向贡献 📉
- **|SHAP值|越大** → 该特征越重要 💎

---

## 📊 输出文件说明

运行分析后，会生成以下文件：

```
output/
├── 📊 statistical_analysis/
│   ├── statistical_metrics.csv       # 统计指标表
│   ├── statistical_report.txt        # 分析报告
│   └── statistical_plots/
│       ├── mean_std_comparison.png           # 均值标准差对比图
│       ├── coefficient_of_variation.png      # 变异系数排序图
│       ├── skewness_kurtosis_scatter.png     # 偏度峰度散点图
│       └── data_distribution_heatmap.png     # 数据分布热图
├── 🔗 correlation_analysis/
│   ├── correlation_matrix.csv         # 相关性矩阵
│   └── correlation_network.pdf        # 相关性网络图
└── 🎯 shap_analysis_output/
    ├── regression_fit.png            # 回归拟合图
    ├── feature_importance.png         # 特征重要性图
    ├── feature_importance.csv         # 特征重要性表
    └── dependence_plots/             # 依赖图文件夹
        ├── dependence_特征1.png
        ├── dependence_特征2.png
        └── ...
```

---

## ⚙️ 高级配置

### 自定义XGBoost超参数

```python
param_grid = {
    'n_estimators': [100, 300, 500],
    'max_depth': [3, 5, 10],
    'learning_rate': [0.01, 0.05, 0.1],
    'subsample': [0.8, 0.9, 1.0],
    'colsample_bytree': [0.8, 0.9, 1.0]
}
analyzer.train_model(param_grid=param_grid)
```

### 切换相关性分析方法

```python
# Pearson（默认，线性相关）
analyzer.set_method('pearson')

# Spearman（单调相关）
analyzer.set_method('spearman')

# Kendall（秩相关）
analyzer.set_method('kendall')
```

### 自定义可视化样式

```python
# 切换颜色方案（1-5）
analyzer.set_visualization_style(scheme_index=2, style_index=3)
```

---

## 🐛 常见问题

### Q1: 报错 "No module named 'xxx'"？
**A:** 请确保安装了所有依赖包：
```bash
pip install -r requirements.txt
```

### Q2: SHAP计算内存不足？
**A:** 减少测试集比例：
```python
analyzer = SHAPAnalyzer(X, y, test_size=0.1)  # 只用10%作为测试集
```

### Q3: 生成的图表中文乱码？
**A:** 确保系统中安装了中文字体，或手动设置字体：
```python
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
```

---

## 📈 性能建议

| 数据量 | 统计分析 | 相关性分析 | SHAP分析 |
|--------|----------|------------|----------|
| < 1000 | ⚡ 快 | ⚡ 快 | ⚡ 快 |
| 1000-5000 | ⚡ 快 | ⚡ 快 | 🚀 中 |
| 5000-10000 | ⚡ 快 | 🚀 中 | 🐢 慢 |
| > 10000 | ⚡ 快 | 🐢 慢 | 🐌 很慢 |

**建议：** 大数据集时考虑采样或使用更强大的计算资源 💻

---

## 🤝 贡献指南

欢迎贡献代码、报告 Bug 或提出建议！

### 代码规范

- 遵循 PEP 8 规范
- 添加必要的注释和文档字符串
- 编写单元测试
- 确保示例代码可运行

## 📜 License | 许可证

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

**MIT License** - 欢迎贡献！| Welcome contributions!

---

<p align="center">
  <sub>Made with ❤️ for the Blast Furnace Industry | 为高炉炼铁行业而生</sub>
</p>

