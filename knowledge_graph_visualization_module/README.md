# 🔥 GenBFKit — 知识图谱可视化模块

> *"把 2128 个高炉参数从电子表格的噩梦中解救出来，变成一张会呼吸的知识图谱——每次只关注一个注意力头。"*

---

## 🎯 这是什么？

本模块将 GenBFKit 的**五级链式数据字典**转化为可交互、可智能分析的知识图谱。它不仅是好看的图表——它是一套**"静态知识展示 → 动态关联挖掘 → 异常溯源推理"三位一体**的应用体系，帮助高炉操作人员和研究人员既见森林，又见树木。

打个比方：**给高炉数据装上 X 光透视眼 + 第六感预警。**

### 数据字典链式架构

```
工序类型 (8) → 数据类别 (98) → 数据池 (9) → 数据集/核心参数 (2128) → 数据属性 (49)
```

2128 个参数中的每一个？都已映射、关联、随时可探索。

---

## ✨ 核心能力

| 功能 | 作用 | 为何重要 |
|------|------|----------|
| 🗺️ **静态知识展示** | 将完整的五级层级架构渲染为精美的 matplotlib 图谱 | 一眼纵览高炉全流程数据体系 |
| 🕸️ **交互式探索** | 基于 PyVis 的 HTML 可视化，支持缩放、平移、点击、悬停、筛选 | 从"8 大工序类型总览"一路下钻到"3 号风管采样频率是多少？" |
| 🧠 **基于 GAT 的关联发现** | 图注意力网络学习隐藏的工艺耦合关系 | 发现没人想到要定义的关联——比如原料粒度分布如何悄悄影响炉缸侧壁温度 |
| 🔍 **多跳因果推理** | 优先队列 BFS 追溯异常根因 | 从"铁水含硅量超标"到"根因：3 号喷煤管压力 0.2 MPa（正常 0.5 MPa）"，3 分钟搞定，而不是 3 小时 |
| 🎲 **虚拟数据生成器** | 合成遵循 9 类数据池特性的高炉工况数据 | 无需碰生产数据即可验证工作流 |
| 📤 **子图谱导出** | 提取工序类型或数据池专属子图谱 | 聚焦当前任务所需的数据子集 |

---

## 📁 模块结构

```
knowledge_graph_visualization_module/
├── __init__.py                  # 包入口
├── config.py                    # 所有可调参数、路径、配色
├── run.py                       # CLI 命令行入口 (python -m ...)
│
├── data/
│   ├── __init__.py
│   ├── prebuilt_full.json       # 五级数据字典 (8+98+9+2128+49)
│   └── virtual_generator.py     # 合成数据生成器（用于测试验证）
│
├── graph_builder/
│   ├── __init__.py
│   ├── models.py                # 数据模型：GraphNode, GraphEdge, CausalPath 等
│   ├── dictionary_parser.py     # 解析 prebuilt_full.json → 图谱基本元素
│   └── knowledge_graph.py       # 核心知识图谱类（基于 NetworkX）
│
├── gat_engine/
│   ├── __init__.py
│   ├── layers.py                # SparseGATLayer, MultiHeadSparseGATLayer
│   ├── model.py                 # SparseGATLinkPredictionModel
│   └── trainer.py               # GATTrainer：训练 → 发现 → 注入
│
├── causal_reasoning/
│   ├── __init__.py
│   ├── anomaly_detector.py      # 3σ 准则 + 结构性异常检测
│   └── multi_hop_reasoner.py    # 多跳因果路径追溯
│
├── visualizer/
│   ├── __init__.py
│   ├── static_renderer.py       # Matplotlib 静态 PNG 渲染
│   └── interactive_renderer.py  # PyVis 交互式 HTML 渲染
│
├── tests/
│   ├── __init__.py
│   └── test_all.py              # 74 项综合测试套件
│
├── output/                      # （自动创建）生成的可视化产物
└── README.md                    # 英文文档 📍
└── README_CN.md                 # 你在这里 📍
```

> 🏝️ **完全自包含**：本目录完全独立。下载它，安装依赖，开箱即用。无需外部 GenBFKit 项目依赖。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install networkx matplotlib torch pyvis scikit-learn scipy numpy pandas
```

> **GPU 用户**：如有 CUDA，PyTorch 会自动检测。纯 CPU 也没问题——稀疏 GAT 在 CPU 上依然很快。

### 2. 运行演示

```bash
cd knowledge_graph_visualization_module
python -m knowledge_graph_visualization_module.run --mode demo
```

这将执行：
- ✅ 从 `data/prebuilt_full.json` 构建知识图谱（2357 节点，约 6500 条边）
- ✅ 训练 GAT 50 轮（CPU 约需 10 秒）
- ✅ 生成虚拟数据 & 检测异常
- ✅ 追溯异常根因
- ✅ 渲染所有可视化产物到 `output/`

### 3. 探索输出

```bash
open output/hierarchy_overview.png              # 静态总览图
open output/kg_full_interactive.html            # 交互式图谱（浏览器打开）
open output/anomaly_highlight.png               # 异常溯源图
```

---

## 🎮 命令行模式

```bash
# 完整流水线：构建 → GAT → 异常 → 可视化
python -m knowledge_graph_visualization_module.run --mode full

# 仅构建知识图谱
python -m knowledge_graph_visualization_module.run --mode build

# 仅 GAT 关联发现
python -m knowledge_graph_visualization_module.run --mode gat

# 仅异常检测与推理
python -m knowledge_graph_visualization_module.run --mode anomaly

# 仅可视化（假定知识图谱已构建）
python -m knowledge_graph_visualization_module.run --mode visualize

# 快速演示（精简轮次，速度优先）
python -m knowledge_graph_visualization_module.run --mode demo

# 运行综合测试套件
python -m knowledge_graph_visualization_module.run --mode test
```

### 自定义路径

```bash
python -m knowledge_graph_visualization_module.run --mode demo \
    --json-path /path/to/your/prebuilt_full.json \
    --output-dir /path/to/output
```

---

## 🧑‍💻 Python API

### 构建知识图谱

```python
from knowledge_graph_visualization_module import BlastFurnaceKnowledgeGraph

kg = BlastFurnaceKnowledgeGraph()
kg.build_from_prebuilt()

# 查看统计信息
print(kg.summary())
# {'total_nodes': 2357, 'total_edges': 6498, ...}
```

### 链式检索（五级逐层下钻）

```python
from knowledge_graph_visualization_module.graph_builder.models import NodeType

wt_nodes = kg.get_nodes_by_type(NodeType.WORK_TYPE)
result = kg.chain_retrieve(wt_nodes[0].node_id)
# 返回嵌套字典：work_type → categories → datasets → pools
```

### GAT 关联发现

```python
from knowledge_graph_visualization_module import GATTrainer

trainer = GATTrainer(kg, num_epochs=100, threshold=0.7)
trainer.train()
discoveries = trainer.discover_hidden_relations()
trainer.inject_discoveries(discoveries[:20])  # 将前 20 条注入知识图谱
```

### 异常检测与因果推理

```python
from knowledge_graph_visualization_module import AnomalyDetector, MultiHopCausalReasoner

detector = AnomalyDetector(kg)
# 从真实/虚拟时序数据检测
anomaly_ids = detector.detect_from_data({"ds_42": [1.2, 1.3, 15.7, ...]})

reasoner = MultiHopCausalReasoner(kg, max_hops=5)
paths = reasoner.trace_anomaly(anomaly_ids[0])
for path in paths:
    print(f"置信度: {path.confidence:.3f}")
    print(f"根因路径: {path.description}")
```

### 可视化

```python
from knowledge_graph_visualization_module import StaticRenderer, InteractiveRenderer

# 静态 PNG
static = StaticRenderer(kg, output_dir="./my_output")
static.render_hierarchy_overview()
static.render_anomaly_highlight(anomaly_ids)

# 交互式 HTML
interactive = InteractiveRenderer(kg, output_dir="./my_output")
interactive.render_full_graph()
interactive.render_anomaly_trace(anomaly_ids)
```

### 虚拟数据生成器

```python
from knowledge_graph_visualization_module import VirtualDataGenerator

vgen = VirtualDataGenerator(kg, num_timesteps=1000, anomaly_ratio=0.05)
scenario = vgen.generate_full_scenario()
# scenario['data']         → Dict[node_id, np.ndarray]
# scenario['anomaly_ids']  → 异常节点 ID 列表
# scenario['statistics']   → 各参数统计信息
# scenario['metadata']     → 摘要计数
```

---

## 🏗️ 架构详解

### 知识图谱核心

`BlastFurnaceKnowledgeGraph` 封装了一个 **NetworkX DiGraph**，包含：

- **5 种节点类型**：`work_type`、`data_category`、`data_pool`、`dataset`、`data_attribute`
- **4 种边类型**：`hierarchical`（父子层级）、`cross_level`（参数↔池跨层）、`process_coupling`（GAT 发现）、`anomaly_propagation`（因果推理）
- **链式检索**：一次 `chain_retrieve(work_type_id)` 调用即可遍历全部 5 级
- **子图提取**：`get_subgraph_by_work_type()` 和 `get_subgraph_by_pool()` 返回独立的 `BlastFurnaceKnowledgeGraph` 实例

### 稀疏 GAT 引擎

GAT 引擎采用**稀疏注意力机制**（基于边列表），替代密集的 N×N 矩阵运算，在 2000+ 节点图谱上高效运行：

```
复杂度：O(|E|) 而非 O(N²)
前向传播：2357 节点约 40ms（CPU）
```

**架构**：`SparseGATBody` = 2 层多头 GAT + `LinkPredictor`（双线性解码器）

**训练流程**：
1. 编码节点特征（类型独热编码 + 度 + 层级）
2. 从层级边和跨层边构建稀疏边索引
3. 使用正/负样本边的 BCE 损失训练
4. 通过嵌入向量的点积评分发现隐藏关联

### 因果推理引擎

`MultiHopCausalReasoner` 实现了**优先队列 BFS**，具有以下特性：

- **边类型优先级**：anomaly_propagation > process_coupling > hierarchical > cross_level
- **异常加成**：穿越其他异常节点时置信度 +0.2
- **分数衰减**：每跳 ×0.9（惩罚过长路径）
- **去重**：相同终点 → 保留最高置信度路径

`AnomalyDetector` 支持：
- **3σ 统计检测**（基于时序数据）
- **图结构性检测**（度分布异常值）
- **人工标记**（操作员标记的异常）

### 可视化系统

**静态渲染器**（matplotlib）：
- 暗色主题（`#0d1117` 背景，灵感源自 GitHub Dark）
- 色盲友好配色（红/钢蓝/青/金/紫，对应 5 个层级）
- 层级布局，按层级定位节点
- 异常节点红色高亮，金色边框
- 发现的边以橙色虚线展示

**交互式渲染器**（PyVis）：
- ForceAtlas2 布局 + 物理模拟
- 完整的缩放/平移/点击/悬停交互
- 悬停提示框展示节点详情（名称、类型、层级、异常状态）
- 节点/边类型筛选菜单
- 导航按钮 + 键盘控制

---

## 🧪 测试

综合测试套件覆盖 **12 个测试类别，74 项断言**：

```bash
cd knowledge_graph_visualization_module
python -c "
import sys; sys.path.insert(0, '..')
from tests.test_all import run_all_tests
run_all_tests()
"
```

| # | 测试类别 | 断言数 |
|---|---------|--------|
| 1 | 数据字典解析 | 6 |
| 2 | 知识图谱构建与摘要 | 4 |
| 3 | 节点/边查询 | 7 |
| 4 | 链式检索 | 4 |
| 5 | 子图提取 | 3 |
| 6 | GAT 训练与关联发现 | 6 |
| 7 | 异常检测与因果推理 | 8 |
| 8 | 虚拟数据生成器 | 15 |
| 9 | 静态可视化 | 4 |
| 10 | 交互式可视化 | 3 |
| 11 | 序列化 | 7 |
| 12 | 端到端流水线 | 4 |

---

## ⚙️ 配置参数

所有参数集中在 `config.py` 中。关键可调项：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `GAT_NUM_HEADS` | 4 | 注意力头数 |
| `GAT_HIDDEN_DIM` | 64 | 隐藏层维度 |
| `GAT_NUM_EPOCHS` | 200 | 训练轮次 |
| `GAT_DISCOVERY_THRESHOLD` | 0.7 | 发现边的最低评分阈值 |
| `CAUSAL_MAX_HOPS` | 5 | 异常溯源最大跳数 |
| `CAUSAL_TOP_K_PATHS` | 10 | 返回的最大因果路径数 |
| `CAUSAL_ANOMALY_ZSCORE_THRESHOLD` | 2.5 | Z 分数阈值（约等于 3σ） |
| `VIRTUAL_NUM_TIMESTEPS` | 1000 | 虚拟数据时间步数 |
| `VIRTUAL_ANOMALY_RATIO` | 0.05 | 异常参数占比 |

---

## 🎨 配色方案

可视化采用精心挑选的色盲友好配色：

| 节点类型 | 颜色 | 色值 |
|----------|------|------|
| 工序类型 (Work Type) | 🔴 红色 | `#E63946` |
| 数据类别 (Data Category) | 🔵 钢蓝 | `#457B9D` |
| 数据池 (Data Pool) | 🟢 青色 | `#2A9D8F` |
| 数据集 (Dataset) | 🟡 金色 | `#E9C46A` |
| 数据属性 (Data Attribute) | 🟣 紫色 | `#8338EC` |

| 边类型 | 颜色 | 样式 |
|--------|------|------|
| 层级关系 (Hierarchical) | 灰色 `#ADB5BD` | 实线，细 |
| 跨层关系 (Cross-Level) | 深灰 `#6C757D` | 实线，细 |
| 工艺耦合 (Process Coupling, GAT 发现) | 橙色 `#FF6B35` | 虚线，粗 |
| 异常传播 (Anomaly Propagation) | 深红 `#D00000` | 虚线，粗 |

---

## 🔬 GAT 关联发现原理（有趣的部分）

传统知识图谱只能展示人工明确定义的关系。但高炉是个复杂的巨系统——存在着没人想到要文档化的隐性耦合。

我们的 GAT 引擎学习哪些参数之间"相互关注"：

1. **输入**：每个节点获得一个特征向量（类型编码 + 图结构信息）
2. **注意力**：多头 GAT 为每条边计算注意力系数 α_ij
3. **嵌入**：两层 GAT 生成 16 维节点嵌入
4. **评分**：对每对候选节点（尚未连接的），计算 `sigmoid(h_i · h_j)`
5. **发现**：评分超过 0.7 的节点对被标记为隐藏工艺耦合

可能发现的关联示例：
- *"烧结矿粒度分布 ↔ 炉缸侧壁 3 号热电偶温度"*
- *"风量设定值 ↔ 瓦斯灰排放浓度"*

这些正是经验丰富的操作员*凭直觉知道*却从未形式化的跨系统关联。现在图谱可以自动发现它们。

---

## 🔍 因果推理原理（救命的部分）

当高炉出了问题，操作员面临一个令人头疼的问题：**"这 2128 个参数里，到底哪个才是罪魁祸首？"**

传统做法：盯仪表盘 1-2 个小时。祝你好运。

我们的做法：

```
异常检测：铁水含硅量 = 0.85%（正常：0.40-0.60%）
    ↓ [跳 1] 同类别关联：铁水温度 = 1562°C（正常：1480-1520°C）
    ↓ [跳 2] 工艺耦合：喷煤速率 = 异常
    ↓ [跳 3] 根因定位：3 号喷煤管压力 = 0.2 MPa（正常：0.5 MPa）
    ✅ 根因定位完成，耗时 < 3 分钟
```

推理器优先级：
1. **异常传播边**（来自先前推理会话的记录）
2. **GAT 发现的工艺耦合边**（隐性但强关联）
3. **层级父节点边**（沿工艺流程向上溯源）
4. **跨层边**（追踪设备关联关系）

---

## 📝 设计说明

### 为什么用稀疏 GAT？

完整图谱有 2357 个节点。密集注意力矩阵是 2357×2357 ≈ 550 万个元素/次前向传播。稀疏版本仅计算实际存在的边（约 1.5 万个元素），实现**约 350 倍加速**。

### 为什么用 NetworkX？

对于 2357 节点的图谱，NetworkX 提供：
- 丰富的图算法（BFS、最短路径、子图提取）
- 简便的序列化
- Python 原生（无需编译）
- 兼容 matplotlib 和 PyVis 双渲染器

对于 10 万+ 节点的生产场景，建议升级至 **igraph** 或 **graph-tool**。

### 自包含独立性

本模块设计为**完全自包含**：
- `data/prebuilt_full.json` 已打包在模块内
- 所有导入要么是 Python 标准库，要么是本目录内的子包
- 运行时不依赖父级 GenBFKit 项目
- 仅下载本文件夹 → 安装依赖 → 即刻可用

---

## 📜 License | 许可证

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

**MIT License** - 欢迎贡献！| Welcome contributions!

---

<p align="center">
  <sub>Made with ❤️ for the Blast Furnace Industry | 为高炉炼铁行业而生</sub>
</p>

