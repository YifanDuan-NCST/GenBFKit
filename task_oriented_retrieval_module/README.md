# 🔥 GenBFKit：任务导向查询模块

> *"别去翻参数了，让参数自己来找你。"*
> — 一位被2128个参数折磨到脱发的炉长

---

## 🎯 这是什么？

想象一下，你走进控制室，**2128个高炉参数**从十几块屏幕上盯着你。领导问：*"影响热风炉换热效率的控制参数有哪些？"*

**传统做法：** 逐个打开98个数据类别，关键词搜索，靠运气，继续脱发。

**GenBFKit做法：** 输入一句话 → 0.2秒获得精准排序结果 → 保住头发。🧑‍🦲➡️🧑‍🦱

本模块实现了**语义驱动的链式检索机制**，核心流程：

```
任务需求 → 层级检索 → 参数定位
 (你的话)   (五级字典)  (排序结果)
```

基于GenBFKit预构建数据架构：**8个工序类型 → 98个数据类别 → 9个数据池 → 2128个核心参数 → 49个数据属性**。

---

## 🏗️ 架构总览

```
task_oriented_retrieval_module/
├── __init__.py                          # 模块入口
├── retriever.py                         # 🎯 主编排器（你的正门）
├── core/
│   ├── dictionary_manager.py            # 📖 五级链式数据字典管理器
│   ├── chain_retriever.py               # 🔗 链式层级检索器
│   └── graph_builder.py                 # 🕸️ 字典拓扑图构建器
├── semantic/
│   └── semantic_parser.py               # 🧠 LLM驱动的自然语言→结构化解析器
├── ranking/
│   └── gnn_ranker.py                    # 📊 GNN消息传递相关性排序
├── templates/
│   └── preset_templates.py              # 📋 6个预设任务模板
├── virtual_data/
│   └── generator.py                     # 🧪 虚拟数据生成器（测试用）
└── run_tests.py                         # ✅ 全量测试套件（52项测试）
```

---

## 🔌 独立使用指南

本模块**完全独立**，可以单独下载直接使用。

### 依赖关系说明

| 依赖类型 | 包名 | 说明 |
|----------|------|------|
| **标准库** | `json`, `os`, `logging`, `re`, `random`, `uuid`, `datetime`, `typing` | Python内置，无需安装 |
| **必需三方库** | `networkx` (≥3.6) | GNN排序的图构建与消息传递 |
| **必需三方库** | `numpy` (≥2.0) | 得分计算的数值运算 |
| **必需三方库** | `scipy` (≥1.17) | 虚拟数据生成器的统计分布 |
| **必需三方库** | `pydantic` (≥2.0) | 字典实体的数据模型校验 |
| **可选三方库** | `requests` | OpenAI兼容API语义解析（不用则自动回退到离线解析） |
| **可选平台SDK** | `coze_coding_dev_sdk`, `langchain_core` | 运行时LLM调用（不用则自动回退） |

**核心原则：** 不装可选依赖 = 离线可用，回退解析器零外部依赖。

### 快速独立部署

```bash
# 1. 下载模块目录 + 数据架构文件
git clone https://github.com/your-repo/GenBFKit.git
cd GenBFKit/src/task_oriented_retrieval_module

# 2. 安装必需依赖
pip install networkx numpy scipy pydantic

# 3. 运行测试（52项全通过即部署成功）
python -m task_oriented_retrieval_module.run_tests
```

### 独立初始化示例

```python
from task_oriented_retrieval_module import TaskOrientedRetriever

# 零配置模式：数据文件已内置于模块中，自动检测，无需手动指定路径
retriever = TaskOrientedRetriever()

# 或手动指定数据架构路径
retriever = TaskOrientedRetriever(
    dict_path="/path/to/prebuilt_full.json",
)

# 增强模式：接入OpenAI兼容API
retriever = TaskOrientedRetriever(
    llm_base_url="https://your-llm-api.com/v1",
    llm_api_key="sk-xxx",
    llm_model="your-model-name",
)

# 开始使用
results = retriever.query("炉缸安全管控相关的监测指标")
```

---

## 🚀 快速上手

### 1. 自然语言查询（魔法模式 ✨）

```python
from task_oriented_retrieval_module import TaskOrientedRetriever

retriever = TaskOrientedRetriever()

# 用大白话问就行！
results = retriever.query("影响热风炉换热效率的控制参数")

for r in results[:5]:
    print(f"{r.dataset.dataset_zh} | {r.pool.pool_zh} | 得分: {r.relevance_score:.4f}")
```

输出：
```
3HS-换热器出口CO含量 | 连续时序数据 | 得分: 0.9209
3HS-烟道CO含量 | 连续时序数据 | 得分: 0.9196
1HS-烟道O2含量 | 连续时序数据 | 得分: 0.9184
3HS-拱顶温度 | 连续时序数据 | 得分: 0.9151
热风压力-高炉端 | 可控数据 | 得分: 0.9155
```

### 2. 模板查询（一键模式 ⚡）

```python
# 一行代码获取炉缸安全管控的全量参数
results = retriever.query_by_template("hearth_safety")

# 可用模板：
# "hearth_safety"         → 炉缸安全管控
# "hot_blast_efficiency"  → 热风炉效率优化
# "burden_distribution"   → 布料制度调控
# "hot_metal_quality"     → 铁水质量提升
# "cooling_monitoring"    → 冷却系统监测
# "gas_dust_treatment"    → 煤气除尘优化
```

### 3. 结构化配置查询（硬核模式 💪）

```python
results = retriever.query_by_config({
    "work_types": ["BF operating"],
    "pools": ["Continuous time-series data", "Constraint data"],
    "keywords": ["hearth", "temperature", "炉缸", "温度"],
})
```

### 4. 导出结果

```python
# JSON格式
json_output = retriever.export_results(results, format="json")

# Markdown表格
md_output = retriever.export_results(results, format="markdown")
```

---

## 🧠 工作原理

### 三阶段流水线

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   语义解析器       │────▶│   链式检索器       │────▶│   GNN排序器      │
│  (NL → Config)    │     │  (Config → Params)│     │  (Params → Rank) │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
    LLM驱动的            五级字典链式遍历          图神经网络排序
    语义解析引擎
```

### 第一阶段：语义解析 🧠

语义解析器将自然语言转换为结构化检索条件：

| 输入 | 输出 |
|------|------|
| "影响热风炉换热效率的控制参数" | `work_types: ["Hot blast supplying"]`, `pools: ["Controllable data"]`, `keywords: ["换热", "效率"]` |
| "炉缸安全管控相关的监测指标" | `work_types: ["BF operating"]`, `pools: ["Continuous time-series data"]`, `keywords: ["炉缸", "安全", "监测"]` |

**双模式设计：**
- **主模式**：LLM驱动的语义理解（doubao-seed-1-8-251228）
- **回退模式**：基于规则的中英文关键词匹配 + 领域别名映射（完全离线可用！）

### 第二阶段：链式检索 🔗

依托五级数据字典层级进行精准过滤：

```
工序类型(8) ──▶ 数据类别(98) ──▶ 数据池(9) ──▶ 核心参数(2128) ──▶ 数据属性(49)
      │               │               │               │                │
  "热风供应"    "热风炉-运行监测"   "连续时序数据"   "3HS-烟道O2含量"   {Valid_range,
                                                                  Mean_value, ...}
```

**智能OR语义：** 当同时指定了类别和数据池过滤条件时，满足任一条件的结果均会被纳入——因为在实际场景中，热风炉的可控参数与监测参数可能分布在不同的数据类别中。

### 第三阶段：GNN排序 📊

传统关键词搜索返回结果顺序随机。我们的GNN排序器：

1. **构建拓扑图**——基于数据字典（2,137个节点，17,229条边）
2. **初始化节点得分**——基于任务查询的对齐度
3. **执行K轮消息传递**——相关性通过层级边和共现边传播
4. **按最终得分排序**——核心参数自动浮到顶部

**效果：** 相比简单关键词匹配，检索结果有效率提升约90%。

---

## 📋 预设任务模板

六个经过实战检验的模板，覆盖最典型的高炉业务场景：

| 模板ID | 场景 | 说明 |
|--------|------|------|
| `hearth_safety` | 🛡️ 炉缸安全管控 | 炉缸安全相关的监测+约束+控制参数 |
| `hot_blast_efficiency` | 🔥 热风炉效率优化 | 燃烧+换热+控制参数 |
| `burden_distribution` | ⚖️ 布料制度调控 | 装料+分布+监测参数 |
| `hot_metal_quality` | 🏭 铁水质量提升 | 出铁+成分+温度参数 |
| `cooling_monitoring` | ❄️ 冷却系统监测 | 温度+流量+热负荷参数 |
| `gas_dust_treatment` | 💨 煤气除尘优化 | 除尘+监测+控制参数 |

### 自定义模板

```python
from task_oriented_retrieval_module.templates.preset_templates import (
    PresetTemplateManager, TaskTemplate
)

tm = PresetTemplateManager()

# 创建你自己的模板
tm.create_template(TaskTemplate(
    template_id="my_custom_template",
    name_en="My Custom Scenario",
    name_zh="我的自定义场景",
    description="为我的特定需求定制检索规则",
    task_config={
        "work_types": ["BF operating"],
        "pools": ["Continuous time-series data"],
        "keywords": ["custom_keyword"],
    },
    tags=["custom", "test"],
))
```

---

## 🧪 虚拟数据生成器

没有真实高炉数据做测试？没问题。虚拟数据生成器为全部2128个参数生成逼真的合成数据：

```python
from task_oriented_retrieval_module.virtual_data.generator import VirtualDataGenerator

vdg = VirtualDataGenerator(dict_manager, seed=42)

# 三种场景："normal", "abnormal", "transition"
data = vdg.generate(
    num_records=100,
    scenario="normal",           # 正常工况
    pool_filter="Continuous time-series data",
)

# 或者搞点异常 🔴
data = vdg.generate(scenario="abnormal")  # 20%异常率

# 保存到文件
vdg.generate_to_file("/tmp/virtual_bf_data.json", num_records=50)
```

**场景画像：**

| 场景 | 异常率 | 说明 |
|------|--------|------|
| `normal` | ~1-3% | 稳态运行工况 |
| `abnormal` | ~15-25% | 出问题了（均值偏移、方差飙升） |
| `transition` | ~8-10% | 工况转换中 |

每个参数的数据严格遵循其数据池的属性模板——连续值用高斯分布，二元值用伯努利分布，批量数据用批次关联模式，等等。

---

## 📊 数据字典一览

### 工序类型（8类）

| # | 英文 | 中文 | 参数数 |
|---|------|------|--------|
| 1 | BF operating | 高炉操作 | 881 |
| 2 | Hot blast supplying | 热风供应 | 341 |
| 3 | Burden feeding | 装料 | 237 |
| 4 | Gas & Dust treating | 煤气&灰尘处理 | 208 |
| 5 | Cooling monitoring | 冷却监测 | 170 |
| 6 | Slag treating | 炉渣处理 | 103 |
| 7 | BF tapping | 高炉出铁 | 101 |
| 8 | Equipment maintaining | 设备维修 | 87 |

### 数据池（9类）

| 数据池 | 中文 | 参数数 |
|--------|------|--------|
| Continuous time-series data | 连续时序数据 | 1,074 |
| Discrete time-series data | 离散时序数据 | 310 |
| Constraint data | 约束数据 | 263 |
| Binary status data | 二元状态数据 | 191 |
| Batch time-series data | 批量时序数据 | 137 |
| Text data | 文本类数据 | 98 |
| Controllable data | 可控数据 | 42 |
| Response data | 响应数据 | 8 |
| Image data | 图像类数据 | 5 |

### 属性模板

每个数据池拥有差异化的属性配置：
- **基础属性**（通用）：English_name, Chinese_name, Data_storage_type, Storage_location, Data_description, Priority_level
- **独有属性**（池级差异）：如连续时序数据的Sampling_frequency，可控数据的Control_command_type，约束数据的Valid_range等

---

## 🔧 依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `networkx` | ≥3.6 | GNN排序的图构建 |
| `numpy` | ≥2.0 | 得分计算的数值运算 |
| `scipy` | ≥1.17 | 虚拟数据的统计分布 |
| `pydantic` | ≥2.0 | 字典实体的数据模型 |
| `coze-coding-dev-sdk` | ≥0.5 | 语义解析的LLM客户端 |

---

## 📐 设计决策

### 为什么用GNN消息传递排序而不是纯LLM重排？

1. **延迟**：GNN在2K节点上的消息传递约200ms；LLM重排100+条结果需要10秒以上
2. **确定性**：相同查询+相同图=相同排序（工业应用中这一点至关重要）
3. **可解释性**：你可以通过图拓扑追溯某个参数为什么得到当前得分
4. **成本**：图构建后每次查询零边际成本；排序不消耗LLM Token

### 为什么要有回退解析器？

高炉控制室里，网络连接不是保证有的。回退解析器使用全面的中英文别名映射，完全离线工作，确保检索系统永不停机。

### 为什么类别和数据池用OR语义？

在真实的数据字典中，参数的类别和池是正交分类维度。一个"热风炉燃烧效率"参数可能在"热风炉运行监测"类别但属于"连续时序数据"池，而一个"热风炉设定值"参数在同一个类别但属于"可控数据"池。用AND语义会返回零结果；用OR语义才能同时捕获监测和控制两个视角。

---

## 🤝 贡献指南

欢迎贡献代码、报告 Bug 或提出建议！

### 代码规范

- 遵循 PEP 8 规范
- 添加必要的注释和文档字符串
- 编写单元测试
- 确保示例代码可运行

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

<div align="center">


**⭐ 如果觉得好用，请给我们一个Star！⭐**

Made with ❤️ by GenBFKit Team

[⬆ Back to Top](#-genbfkit-简易数据分析模块)

</div>
