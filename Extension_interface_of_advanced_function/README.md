# 🔌 GenBFKit - Extension Interface of Advanced Function

<p align="center">
  <img src="https://img.shields.io/badge/GenBFKit-Extension_Interface-blueviolet?style=for-the-badge" alt="GenBFKit">
  <img src="https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/ONNX-Runtime-orange?style=for-the-badge" alt="ONNX">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

> 🚀 **全链路高炉智能开发平台扩展接口体系**
>
> 🔌 **Full-Chain Blast Furnace Intelligent Development Extension Interface System**
>
> 从固定式工具框架向通用可扩展的高炉智能开发平台升级的关键基础设施 | The Critical Infrastructure for Upgrading from Fixed Tool Framework to Extensible BF Intelligent Development Platform

---

## 📑 Table of Contents | 目录

- [🎯 Overview | 项目概述](#-overview--项目概述)
- [✨ Features | 核心特性](#-features--核心特性)
- [🏗️ Architecture | 系统架构](#️-architecture--系统架构)
- [🚀 Quick Start | 快速开始](#-quick-start--快速开始)
- [🔧 Module Details | 模块详解](#-module-details--模块详解)
  - [📦 1. Custom Algorithm Deployment | 自定义算法部署](#1-custom-algorithm-deployment--自定义算法部署)
  - [🔗 2. Upper-level System Integration | 上层系统对接](#2-upper-level-system-integration--上层系统对接)
  - [📐 3. Data Architecture Extension | 底层数据架构拓展](#3-data-architecture-extension--底层数据架构拓展)
- [📊 Data Model | 数据模型](#-data-model--数据模型)
- [📚 API Reference | API 参考](#-api-reference--api-参考)
- [💡 Use Cases | 使用场景](#-use-cases--使用场景)
- [📂 File Structure | 文件结构](#-file-structure--文件结构)
- [📜 License | 许可证](#-license--许可证)

---

## 🎯 Overview | 项目概述

**Extension Interface of Advanced Function** 是 GenBFKit 框架的高级功能扩展接口体系，基于**松耦合的模块化架构**构建全链路标准化的扩展接口，为 GenBFKit 从固定式工具框架向通用可扩展的高炉智能开发平台升级奠定基础。

本模块将 GenBFKit 的前置 6 个核心模块功能独立封装，通过底层数据字典完成数据交互，支持自定义修改、功能替换与场景拓展。涵盖 **3 类标准化扩展接口**：

The **Extension Interface of Advanced Function** is a full-chain standardized extension interface system built on a **loosely coupled modular architecture**, providing the foundation for upgrading GenBFKit from a fixed tool framework to a general-purpose extensible BF intelligent development platform.

Three standardized extension interfaces are designed:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    🔌 Extension Interface of Advanced Function               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1️⃣ 自定义算法部署          2️⃣ 上层系统对接           3️⃣ 底层数据架构拓展      │
│  Custom Algorithm          Upper-level System        Data Architecture      │
│  Deployment                Integration               Extension              │
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │ • ONNX 推理引擎    │    │ • 数据发布总线     │    │ • 架构校验管理     │      │
│  │ • 模型注册中心     │    │ • 数字孪生适配     │    │ • CRUD 操作       │      │
│  │ • 特征自动组装     │    │ • 领域大模型接口    │    │ • 外部数据映射     │      │
│  │ • 推理流水线       │    │ • 全链闭环引擎     │    │                  │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features | 核心特性

### 🔥 Core Capabilities | 核心能力

| ✨ Feature | 📝 Description | 🎯 功能说明 |
|------------|----------------|------------|
| 🧠 **ONNX 算法部署** | Deploy ONNX models with auto feature assembly | ONNX 格式模型一键部署，自动特征组装与数据链路对接 |
| 🗂️ **模型注册中心** | Centralized model registry with versioning | 集中式模型注册管理，支持版本控制与元数据查询 |
| 📡 **数据发布总线** | Pub-Sub data bus for cross-system communication | 发布-订阅数据总线，实现跨系统实时数据流通 |
| 🏭 **数字孪生对接** | Bidirectional digital twin interface | 数字孪生平台双向适配，数据推送与策略反向写入 |
| 🤖 **领域大模型集成** | LLM strategy parsing and integration | 领域大模型策略解析，工艺优化指令智能翻译 |
| 🔄 **全链闭环保活** | End-to-end closed-loop orchestration | 数据治理→分析→推理→决策→反馈全链路闭环 |
| ✅ **架构校验** | Pydantic-validated schema management | Pydantic 驱动的架构校验，保证数据完整性 |
| 🔧 **CRUD 拓展** | Full CRUD for dictionary hierarchy | 数据字典全层级增删改查，灵活适配新场景 |
| 🗺️ **外部数据映射** | Auto-detect and map external data sources | 自动识别外部数据特征并映射至数据字典 |

### 📊 Technology Stack | 技术栈

| 🛠️ Technology | 📁 Module | 🎯 Purpose | 用途 |
|---------------|-----------|------------|------|
| 🧠 **ONNX Runtime** | `model_deployment/` | Cross-framework model inference | 跨框架模型推理引擎 |
| 📦 **Pydantic** | `data_extension/` | Schema validation & data modeling | 架构校验与数据建模 |
| ⚡ **FastAPI** | `system_integration/` | RESTful API for system integration | RESTful 系统集成接口 |
| 📡 **Pub-Sub 架构** | `system_integration/` | Event-driven data distribution | 事件驱动数据分发 |
| 🔄 **ONNX 格式** | `model_deployment/` | Universal model interchange format | 通用模型交换格式 |

---

## 🏗️ Architecture | 系统架构

### System Architecture | 系统架构图

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                         🔌 Extension Interface of Advanced Function                 │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                    📦 Core Layer (核心层)                                      │   │
│  │  ┌──────────────────────────────────────────────────────────────────────┐   │   │
│  │  │  DataDictionary · Config · Prebuilt Data Arch (2128 params)        │   │   │
│  │  └──────────────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                                    │
│          ┌─────────────────────────┼─────────────────────────┐                        │
│          ▼                         ▼                         ▼                        │
│  ┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐           │
│  │ Model Deployment │    │ System Integration   │    │ Data Extension     │           │
│  │   算法部署模块    │    │    系统对接模块      │    │   数据拓展模块      │           │
│  ├─────────────────┤    ├─────────────────────┤    ├─────────────────────┤           │
│  │ • ONNXEngine    │    │ • DataBus (Pub-Sub)  │    │ • SchemaManager    │           │
│  │ • ModelRegistry │    │ • DigitalTwinAdapter │    │ • DictionaryCRUD   │           │
│  │ • FeatureAsmblr │    │ • LLMAdapter         │    │ • DataMapper       │           │
│  │ • InferencePipe │    │ • ClosedLoopEngine   │    │                     │           │
│  └─────────────────┘    └─────────────────────┘    └─────────────────────┘           │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │   📡 External Integrations (外部对接)                                          │   │
│  │   PyTorch · TensorFlow · Scikit-learn · Digital Twin · Domain LLM · ...     │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Core Classes | 核心类说明

| 🏷️ Class | 📁 File | 🎯 Responsibility | 职责 |
|-----------|---------|------------------|------|
| `ONNXEngine` | `model_deployment/onnx_engine.py` | ONNX model loading, inference, session management | ONNX 模型加载、推理与会话管理 |
| `ModelRegistry` | `model_deployment/model_registry.py` | Model registration, versioning, query | 模型注册、版本控制与查询检索 |
| `FeatureAssembler` | `model_deployment/feature_assembler.py` | Auto feature extraction & assembly | 自动特征提取与特征组装 |
| `InferencePipeline` | `model_deployment/inference_pipeline.py` | End-to-end model inference pipeline | 端到端模型推理流水线编排 |
| `DataBus` | `system_integration/data_bus.py` | Pub-Sub message distribution | 发布-订阅消息分发总线 |
| `DigitalTwinAdapter` | `system_integration/digital_twin_adapter.py` | Bidirectional twin platform interface | 数字孪生平台双向适配接口 |
| `LLMAdapter` | `system_integration/llm_adapter.py` | Domain LLM strategy query & parsing | 领域大模型策略查询与解析 |
| `ClosedLoopEngine` | `system_integration/closed_loop.py` | Full closed-loop orchestration | 全链路闭环保活编排引擎 |
| `SchemaManager` | `data_extension/schema_manager.py` | Schema validation & rule management | 架构校验与规则管理 |
| `DictionaryCRUD` | `data_extension/crud_operations.py` | CRUD for dictionary hierarchy | 数据字典全层级增删改查 |
| `DataMapper` | `data_extension/mapper.py` | External data auto-mapping | 外部数据自动检测与映射 |

---

## 🚀 Quick Start | 快速开始

### 📌 Requirements | 环境要求

- 🐍 Python 3.10+
- 📦 numpy >= 1.24.0
- 📦 pandas >= 1.5.0
- 📦 onnxruntime >= 1.15.0
- 📦 pydantic >= 2.0.0

### 🔽 Installation | 安装部署

#### 方式一：Git 克隆（推荐）

```bash
# 1. 克隆项目仓库（请将 <REPO_URL> 替换为实际仓库地址）
git clone <REPO_URL>
cd <REPO_NAME>

# 2. 进入扩展接口模块目录
cd Extension_interface_of_advanced_function

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行演示
python run_demo.py
```

#### 方式二：直接下载 ZIP 包

```bash
# 1. 下载项目 ZIP 包并解压到本地目录（如：D:\GenBFKit）
# 2. 进入项目目录
cd D:\GenBFKit\Extension_interface_of_advanced_function

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行演示
python run_demo.py
```

#### 方式三：独立复制模块使用

本模块完全独立于 GenBFKit 其他组件，支持按需复制单个子模块使用：

```python
# demo.py - 仅使用自定义算法部署功能
import sys
from pathlib import Path

# 将模块目录添加到 sys.path
_current_file = Path(__file__).resolve()
_pkg_dir = _current_file.parent / "Extension_interface_of_advanced_function"

if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

# 仅导入需要的子模块
from model_deployment import ONNXEngine, ModelRegistry
from model_deployment import InferencePipeline, FeatureAssembler

# 创建 ONNX 推理引擎
engine = ONNXEngine()
registry = ModelRegistry()
pipeline = InferencePipeline(engine=engine, registry=registry)
print("Custom algorithm deployment module ready!")
```

### 🎯 Basic Usage | 基本用法

```python
from Extension_interface_of_advanced_function import (
    # 📦 Model Deployment
    ONNXEngine, ModelRegistry, FeatureAssembler, InferencePipeline,
    # 🔗 System Integration
    DataBus, DigitalTwinAdapter, LLMAdapter, ClosedLoopEngine,
    # 📐 Data Extension
    SchemaManager, DictionaryCRUD, DataMapper,
    # 🎯 Core
    DataDictionary, GenBFKitConfig
)

# ✨ 创建核心数据字典 | Create core data dictionary
dictionary = DataDictionary.create_prebuilt()
print(f"Work types: {len(dictionary.work_types)}, "
      f"Data pools: {len(dictionary.data_pools)}, "
      f"Attributes: {len(dictionary.pool_attributes)}")
# 输出示例: Work types: 8, Data pools: 9, Attributes: 72

# 🔧 创建配置 | Create configuration
config = GenBFKitConfig(dictionary=dictionary)

# 🧠 部署 ONNX 模型 | Deploy ONNX model
engine = ONNXEngine()
registry = ModelRegistry()
registry.register_model(
    name="temperature_predictor",
    version="1.0.0",
    model_path="path/to/model.onnx",
    task_type="regression"
)

# 📡 配置数字孪生适配器 | Configure digital twin adapter
twin_adapter = DigitalTwinAdapter(
    push_url="http://twin-platform.example.com/api/data",
    pull_url="http://twin-platform.example.com/api/strategies"
)

# 🔄 运行全链闭环保活 | Run closed-loop engine
loop = ClosedLoopEngine(
    data_bus=DataBus(),
    twin_adapter=twin_adapter,
    llm_adapter=LLMAdapter()
)
loop.execute(loop_id="demo_001", input_data=data_frame)
```

> 💡 **提示**：首次使用建议运行以下脚本查看完整示例输出：
> - `python run_demo.py` - 三模块全功能演示

---

## 🔧 Module Details | 模块详解

### 1. Custom Algorithm Deployment | 自定义算法部署

> **核心思想**：基于 ONNX 通用模型格式，支持 PyTorch、TensorFlow、Scikit-learn 等主流框架模型的**零代码接入**，自动完成数据链路对接、格式校验、时序对齐与特征组装。

#### 1.1 工作流程 | Workflow

```
用户 ONNX 模型 → ONNXEngine 加载 → 自动解析输入/输出维度
    → FeatureAssembler 特征映射 → InferencePipeline 推理
    → 结果返回
```

#### 1.2 核心组件 | Core Components

##### 🔩 ONNXEngine

ONNX 模型推理引擎，负责模型的加载、卸载与高性能推理计算。

```python
from model_deployment import ONNXEngine

engine = ONNXEngine()

# 加载 ONNX 模型 | Load ONNX model
engine.load("path/to/model.onnx", device="cpu")  # or "cuda"

# 运行推理 | Run inference
import numpy as np
input_data = np.random.randn(10, 5).astype(np.float32)
outputs = engine.infer({"input": input_data})
# outputs: Dict[str, np.ndarray]

# 获取模型元信息 | Get model metadata
info = engine.get_model_info()
print(info.inputs)   # [{'name': 'input', 'shape': [None, 5], 'dtype': 'tensor(float)'}]
print(info.outputs)  # [{'name': 'output', 'shape': [None, 1], 'dtype': 'tensor(float)'}]
print(info.model_size_mb)  # 模型文件大小 (MB)

# 卸载模型 | Unload model
engine.unload()
```

##### 🗂️ ModelRegistry

集中式模型注册中心，支持多模型管理、版本控制与元数据查询。

```python
from model_deployment import ModelRegistry

registry = ModelRegistry()

# 注册模型 | Register model
registry.register_model(
    name="blast_temp_predictor",
    version="1.0.0",
    model_path="/models/temp_model.onnx",
    task_type="regression",
    description="高炉铁水温度预测模型"
)

# 查询模型 | Query models
model = registry.get_model("blast_temp_predictor")
# ModelInfo(name='blast_temp_predictor', version='1.0.0', ...)

all_models = registry.list_models()
# [ModelInfo(...), ...]

# 导出注册表 | Export registry
registry.export_registry("registry_backup.json")
```

##### 🔧 FeatureAssembler

特征自动组装器，基于数据字典将原始数据自动映射为模型输入特征。

```python
from model_deployment import FeatureAssembler
import pandas as pd

assembler = FeatureAssembler()

# 添加特征映射 | Add feature mapping
assembler.add_feature(
    name="hot_metal_temp",
    source="blast_furnace_data",
    transform="minmax"  # 归一化方式: none | minmax | zscore | robust
)

assembler.add_feature(
    name="blast_pressure",
    source=["pressure_sensor_1", "pressure_sensor_2"],
    transform="zscore",
    aggregation="mean"  # 多源聚合方式: mean | median | max | min
)

# 组装特征 | Assemble features
raw_data = pd.DataFrame({
    "blast_furnace_data": [1520, 1535, 1518],
    "pressure_sensor_1": [0.45, 0.47, 0.44],
    "pressure_sensor_2": [0.44, 0.46, 0.43]
})
features = assembler.assemble(raw_data)
# features: Dict[str, np.ndarray]
```

##### ⚙️ InferencePipeline

端到端推理流水线，将特征组装、模型推理、后处理全链路封装。

```python
from model_deployment import InferencePipeline

pipeline = InferencePipeline(engine=engine, registry=registry)

# 配置流水线 | Configure pipeline
pipeline.configure(
    pipeline_name="temperature_prediction",
    model_name="blast_temp_predictor",
    model_version="1.0.0",
    features=[
        {"name": "hot_metal_temp", "source": "sensor_data", "transform": "minmax"},
        {"name": "blast_pressure", "source": "sensor_data", "transform": "zscore"},
    ]
)

# 执行推理 | Execute prediction
result = pipeline.predict({"sensor_data": raw_df})
# InferenceResult(success=True, latency_ms=23.0, outputs={'output': array(...)})
```

---

### 2. Upper-level System Integration | 上层系统对接

> **核心思想**：预留数字孪生平台与高炉领域大模型双向适配接口，构建"数据治理→智能分析→模型推理→工艺决策→效果反馈"全链路闭环。

#### 2.1 工作流程 | Workflow

```
外部数据 → DataBus 分发 → DigitalTwinAdapter 推送/拉取
    → LLMAdapter 策略解析 → ClosedLoopEngine 闭环编排
    → 结果反馈回数字孪生平台
```

#### 2.2 核心组件 | Core Components

##### 📡 DataBus

发布-订阅数据总线，支持跨系统、跨模块的实时数据分发。

```python
from system_integration import DataBus

bus = DataBus()

# 订阅频道 | Subscribe to channel
def on_data(message):
    print(f"Received: {message['payload']['temperature']}°C")

sub_id = bus.subscribe("blast_furnace_data", callback=on_data)

# 发布消息 | Publish message
bus.publish("blast_furnace_data", {
    "temperature": 1520,
    "pressure": 0.45,
    "flow": 3200,
    "timestamp": "2026-05-25T08:00:00Z"
})

# 获取频道统计 | Get channel stats
stats = bus.get_channel_stats()
# {'blast_furnace_data': 1}

# 取消订阅 | Unsubscribe
bus.unsubscribe(sub_id)
```

##### 🏭 DigitalTwinAdapter

数字孪生平台双向适配器，支持标准化数据推送与优化策略拉取。

```python
from system_integration import DigitalTwinAdapter
import pandas as pd

adapter = DigitalTwinAdapter(
    push_url="http://twin-platform:8080/api/data",
    pull_url="http://twin-platform:8080/api/strategies",
    api_key="your_api_key_here",
    timeout=30
)

# 推送数据到数字孪生 | Push data to digital twin
df = pd.DataFrame({
    "temperature": [1520, 1535],
    "pressure": [0.45, 0.47],
    "flow_rate": [3200, 3250]
})
result = adapter.push_data(df, frame_id="batch_001")
# {'success': True, 'received_at': '...', 'frame_id': 'batch_001'}

# 从数字孪生拉取优化策略 | Pull optimization strategy
strategy = adapter.pull_strategy(context={"hearth_temp": 1520})
# StrategyResult(parameters={...}, rationale="...")
```

##### 🤖 LLMAdapter

领域大模型接口适配器，支持工艺优化策略查询与自然语言指令解析。

```python
from system_integration import LLMAdapter

llm = LLMAdapter(
    api_endpoint="http://llm-service:8000/v1/chat",
    api_key="your_llm_key"
)

# 查询工艺策略 | Query process strategy
response = llm.query_strategy(
    context="Hearth temperature is 1480°C, below optimal range of 1500-1550°C",
    focus="temperature_adjustment"
)
# LLMResponse(success=True, structured_data={...})

# 解析自然语言指令 | Parse natural language command
commands = llm.parse_command(
    "Increase hot blast temperature to 1200°C and set oxygen enrichment to 25%"
)
# ParsedCommand(commands=[...], priority="high", rationale="...")
```

##### 🔄 ClosedLoopEngine

全链路闭环保活引擎，编排"数据摄取→治理→分析→推理→决策→反馈"6 阶段。

```python
from system_integration import ClosedLoopEngine

loop = ClosedLoopEngine(
    data_bus=bus,
    twin_adapter=adapter,
    llm_adapter=llm
)

# 执行单次闭环 | Execute single loop
result = loop.execute(
    loop_id="monitor_cycle_001",
    input_data=raw_dataframe,
    phases=["data_ingestion", "governance", "analysis",
            "inference", "decision", "feedback"]
)
# LoopResult(id='monitor_cycle_001', duration_ms=...,
#            analysis_status='✓', decision_status='✓')
```

---

### 3. Data Architecture Extension | 底层数据架构拓展

> **核心思想**：支持外部高炉场景的数据快速映射、自主适配与架构迭代，依托数据字典的 CRUD 机制，极大提升跨场景迁移能力。

#### 3.1 工作流程 | Workflow

```
外部场景数据 → SchemaManager 校验 → DictionaryCRUD 增/删/改/查
    → DataMapper 自动映射 → 注册至数据字典
```

#### 3.2 核心组件 | Core Components

##### ✅ SchemaManager

架构校验管理器，基于 Pydantic 模型确保数据字典层级结构的完整性与正确性。

```python
from data_extension import SchemaManager

validator = SchemaManager()

# 校验工种 | Validate work type
errors, warnings = validator.validate_work_type("Blast_Furnace")
# if errors: print(errors)

# 校验数据类别 | Validate data category
errors, warnings = validator.validate_category(
    "Process system - Blast furnace - Temperature monitoring"
)
# ✓ Valid

# 校验数据池 | Validate data pool
errors, warnings = validator.validate_pool("Continuous time-series data")
# ✓ Valid

# 获取校验规则 | Get validation rules
rules = validator.get_rules()
```

##### 🔧 DictionaryCRUD

数据字典增删改查操作器，支持 5 层数据层级的全量 CRUD 操作。

```python
from data_extension import DictionaryCRUD

crud = DictionaryCRUD()

# ➕ 添加工种 | Add work type
result = crud.add_work_type(dictionary, "New process type", "新工艺类型")
# Work type 'New process type' added successfully

# ➕ 添加数据类别 | Add data category
result = crud.add_category(
    dictionary, "New process type",
    "New system - New equipment - Temperature monitoring",
    "新系统-新设备-温度监测"
)

# ➕ 添加数据集 | Add dataset
result = crud.add_dataset(
    dictionary, "New process type",
    "New system - New equipment - Temperature monitoring",
    "Continuous time-series data",
    "cooling_water_inlet_temp", "冷却水入口温度"
)

# ➕ 批量添加 | Bulk add datasets
results = crud.bulk_add_datasets(dictionary, [
    {"category": "...", "pool": "...", "name": "param_1", "name_zh": "参数1"},
    {"category": "...", "pool": "...", "name": "param_2", "name_zh": "参数2"},
])
# {'success': 2, 'failed': 0}

# 🔍 搜索 | Search
datasets, attrs = crud.search(dictionary, "temperature")
```

##### 🗺️ DataMapper

外部数据自动映射器，自动检测外部数据结构与数据字典的对应关系。

```python
from data_extension import DataMapper

mapper = DataMapper()

# 检测数据池类型 | Detect pool type
pool_type = mapper.detect_pool_type(
    columns=["timestamp", "value", "quality_flag"]
)
# 'Continuous time-series data'

# 自动映射列 | Auto-map columns
mappings = mapper.auto_map(
    external_columns=["hot_metal_temp", "blast_pressure_MPa"],
    dictionary=dictionary
)
# List[MappingRule(confidence=0.95, ...)]

# 执行全量映射 | Execute full mapping
result = mapper.execute_mapping(
    external_data=df,
    dictionary=dictionary
)
# MappingResult(mapped=3, unmapped=[], warnings=0)
```

---

## 📊 Data Model | 数据模型

### Core Data Classes | 核心数据类

| 🏷️ Class | 📝 Description | 说明 |
|-----------|----------------|------|
| `DataDictionary` | 5-tier hierarchical dictionary structure | 5 级数据字典结构（工种→类别→池→数据集→属性） |
| `GenBFKitConfig` | Configuration holder for module settings | 模块配置持有者 |
| `ONNXModelInfo` | ONNX model metadata (inputs, outputs, size) | ONNX 模型元数据（输入输出维度、大小） |
| `ModelInfo` | Model registration info (name, version, task) | 模型注册信息（名称、版本、任务类型） |
| `FeatureMapping` | Feature source & transform definition | 特征来源与变换定义 |
| `InferenceResult` | Pipeline inference output with latency | 流水线推理输出（含延迟） |
| `BusMessage` | Data bus message with metadata | 数据总线消息（含元数据） |
| `TwinDataFrame` | Digital twin data exchange format | 数字孪生数据交换格式 |
| `StrategyResult` | Strategy query result from twin platform | 数字孪生策略查询结果 |
| `LLMResponse` | LLM API response with structured data | 大模型 API 响应（含结构化数据） |
| `LoopResult` | Closed-loop engine execution result | 闭环引擎执行结果 |
| `MappingRule` | Auto-mapping rule with confidence | 自动映射规则（含置信度） |
| `MappingResult` | Full mapping execution result | 全量映射执行结果 |

---

## 📚 API Reference | API 参考

### 📦 Module: `model_deployment` | 模型部署模块

```python
# ONNXEngine
ONNXEngine(providers=None, inter_op_threads=4, intra_op_threads=4)
├── .load(model_path: str, device: str = "cpu") -> None
├── .infer(inputs: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]
├── .get_model_info() -> ONNXModelInfo
├── .unload() -> None
└── .is_loaded() -> bool

# ModelRegistry
ModelRegistry()
├── .register_model(name, version, model_path, task_type, **meta) -> ModelInfo
├── .get_model(name: str, version: str = None) -> Optional[ModelInfo]
├── .list_models(task_type: str = None) -> List[ModelInfo]
├── .unregister_model(name: str, version: str = None) -> bool
├── .export_registry(path: str) -> None
└── .load_registry(path: str) -> None

# FeatureAssembler
FeatureAssembler()
├── .add_feature(name, source, transform='none', aggregation=None) -> None
├── .remove_feature(name: str) -> bool
├── .assemble(data: pd.DataFrame) -> Dict[str, np.ndarray]
├── .get_feature_config() -> Dict
└── .clear() -> None

# InferencePipeline
InferencePipeline(engine, registry)
├── .configure(pipeline_name, model_name, model_version, features) -> None
├── .predict(inputs: Dict[str, pd.DataFrame]) -> InferenceResult
├── .get_config() -> Dict
└── .validate() -> bool
```

### 🔗 Module: `system_integration` | 系统集成模块

```python
# DataBus
DataBus()
├── .subscribe(channel, callback, filter_fn=None) -> str
├── .publish(channel, payload, msg_type='data_push') -> int
├── .unsubscribe(sub_id: str) -> bool
├── .get_channel_stats() -> Dict[str, int]
└── .clear() -> None

# DigitalTwinAdapter
DigitalTwinAdapter(push_url, pull_url, api_key='', timeout=30)
├── .push_data(data: pd.DataFrame, frame_id=None) -> Dict
├── .pull_strategy(context: Dict = None) -> StrategyResult
├── .health_check() -> bool
└── .set_auth_token(token: str) -> None

# LLMAdapter
LLMAdapter(api_endpoint, api_key, model='gpt-4', timeout=60)
├── .query_strategy(context: str, focus: str = None) -> LLMResponse
├── .parse_command(nl_command: str) -> ParsedCommand
└── .health_check() -> bool

# ClosedLoopEngine
ClosedLoopEngine(data_bus, twin_adapter, llm_adapter)
├── .execute(loop_id, input_data, phases=None) -> LoopResult
├── .get_history(loop_id: str = None) -> List[LoopResult]
└── .reset() -> None
```

### 📐 Module: `data_extension` | 数据拓展模块

```python
# SchemaManager
SchemaManager()
├── .validate_work_type(name: str) -> Tuple[List, List]
├── .validate_category(name: str) -> Tuple[List, List]
├── .validate_pool(name: str) -> Tuple[List, List]
├── .validate_mapping(ext_cols: List[str], dict_cols: List[str]) -> Tuple[List, List]
└── .get_rules() -> Dict

# DictionaryCRUD
DictionaryCRUD()
├── .add_work_type(dict_obj, name, name_zh, **meta) -> str
├── .add_category(dict_obj, work_type, name, name_zh) -> str
├── .add_pool(dict_obj, name, name_zh, base_attrs=None) -> str
├── .add_dataset(dict_obj, work_type, category, pool, name, name_zh) -> str
├── .add_attribute(dict_obj, pool, attr_name, **meta) -> str
├── .bulk_add_datasets(dict_obj, items: List[Dict]) -> Dict
├── .search(dict_obj, keyword: str) -> Tuple[List, List]
├── .remove(dict_obj, item_type, item_id) -> bool
└── .get_summary(dict_obj) -> Dict

# DataMapper
DataMapper()
├── .detect_pool_type(columns: List[str], data_sample=None) -> Optional[str]
├── .auto_map(external_columns: List[str], dictionary) -> List[MappingRule]
├── .execute_mapping(external_data: pd.DataFrame, dictionary) -> MappingResult
└── .save_mapping_rules(rules: List[MappingRule], path: str) -> None
```

---

## 💡 Use Cases | 使用场景

### 🏭 场景一：自定义模型快速部署 | Custom Model Rapid Deployment

**场景**：工艺工程师训练了一个基于 Transformer 的铁水质量预测模型（PyTorch），需要快速部署到 GenBFKit 框架中。

**方案**：
1. 将 PyTorch 模型导出为 ONNX 格式
2. 通过 `ModelRegistry.register_model()` 注册模型
3. 通过 `FeatureAssembler` 配置特征映射
4. 通过 `InferencePipeline.predict()` 一键推理

**优势**：部署周期从传统 15-30 天缩短至**数小时内**，无需编写底层适配代码。

### 🔄 场景二：数字孪生闭环优化 | Digital Twin Closed-Loop Optimization

**场景**：高炉现场需要基于实时数据驱动数字孪生仿真，并将优化策略回写到控制系统。

**方案**：
1. `DataBus` 实时采集现场 PLC 数据并分发
2. `DigitalTwinAdapter.push_data()` 推送至数字孪生平台
3. 数字孪生仿真计算优化策略
4. `DigitalTwinAdapter.pull_strategy()` 拉取策略
5. `ClosedLoopEngine` 完成策略验证与反馈

**优势**：形成"数据→仿真→策略→控制→反馈"的**全链路智能化闭环**。

### 📐 场景三：新高炉场景快速适配 | New BF Scenario Adaptation

**场景**：GenBFKit 需要从 2500m³ 高炉迁移适配到 1080m³ 高炉，设备配置与参数体系存在差异。

**方案**：
1. 通过 `DictionaryCRUD` 在现有字典基础上增删改参数
2. 通过 `SchemaManager` 验证新增架构的完整性
3. 通过 `DataMapper` 自动映射外部数据源

**优势**：**无需重构数据架构**，基于统一规范即可完成新场景的快速适配与迭代。

---

## 📂 File Structure | 文件结构

```
Extension_interface_of_advanced_function/
│
├── __init__.py                      # 🔌 包统一导出入口
├── README.md                        # 📖 本说明文档
├── requirements.txt                 # 📦 依赖声明
├── run_demo.py                      # 🚀 模块独立运行演示脚本
│
├── core/                            # 🎯 核心层
│   ├── __init__.py
│   ├── config.py                    # GenBFKitConfig 配置管理
│   └── data_dictionary.py           # DataDictionary 数据字典核心
│
├── model_deployment/                # 🧠 自定义算法部署模块
│   ├── __init__.py
│   ├── onnx_engine.py               # ONNX Runtime 推理引擎
│   ├── model_registry.py            # 模型注册中心
│   ├── feature_assembler.py         # 特征自动组装器
│   └── inference_pipeline.py        # 端到端推理流水线
│
├── system_integration/              # 🔗 上层系统对接模块
│   ├── __init__.py
│   ├── data_bus.py                  # 发布-订阅数据总线
│   ├── digital_twin_adapter.py      # 数字孪生双向适配器
│   ├── llm_adapter.py               # 领域大模型接口
│   └── closed_loop.py               # 全链路闭环保活引擎
│
├── data_extension/                  # 📐 底层数据架构拓展模块
│   ├── __init__.py
│   ├── schema_manager.py            # 架构校验管理器
│   ├── crud_operations.py           # 字典 CRUD 操作器
│   └── mapper.py                    # 外部数据映射器
│
└── tests/                           # ✅ 单元测试
    └── test_all.py                  # 全部 41 个测试用例
```

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

