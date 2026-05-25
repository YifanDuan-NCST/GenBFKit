# 🎯 GenBFKit - Construction Data Dictionary

<p align="center">
  <img src="https://img.shields.io/badge/GenBFKit-Data_Dictionary-blue?style=for-the-badge" alt="GenBFKit">
  <img src="https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

> 🌟 **层级式高炉炼铁工业数据字典系统**
>
> 🔥 **Hierarchical Blast Furnace Ironmaking Industrial Data Dictionary**
>
> 一站式解决高炉炼铁领域的数据碎片化、处理、整合与使用问题 | One-Stop Solution for Data Fragmentation in BF Ironmaking

---

## 📑 Table of Contents | 目录

- [🎯 Overview | 项目概述](#-overview--项目概述)
- [✨ Features | 核心特性](#-features--核心特性)
- [🏗️ Architecture | 系统架构](#️-architecture--系统架构)
- [🚀 Quick Start | 快速开始](#-quick-start--快速开始)
- [🔧 Advanced Usage | 高级用法](#-advanced-usage--高级用法)
- [📊 Data Model | 数据模型](#-data-model--数据模型)
- [📚 API Reference | API 参考](#-api-reference--api-参考)
- [💡 Use Cases | 使用场景](#-use-cases--使用场景)
- [📂 File Structure | 文件结构](#-file-structure--文件结构)
- [📜 License | 许可证](#-license--许可证)

---

## 🎯 Overview | 项目概述

GenBFKit 提供一套面向 **高炉炼铁场景** 的层级式数据字典，以统一结构组织工业数据。

GenBFKit provides a hierarchical data dictionary for **blast furnace ironmaking scenarios**, organizing industrial data in a unified structure.

系统采用 **5 层数据层级结构**，从宏观到微观依次为：

The system adopts a **5-level data hierarchy**, from macro to micro:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🧑‍🏭 Work Type (工种)          Top-level business scenario                 │
│      └── 📂 Data Category (数据类别)   System / Equipment / Function          │
│            └── 🗃️ Data Pool (数据池)    Data type template                    │
│                  └── 📊 Dataset (数据集)  Collectible / storable data points  │
│                        └── 📋 Attribute (属性模板)  Field attributes by pool  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features | 核心特性

### 🔥 Core Capabilities | 核心能力

| ✨ Feature | 📝 Description | 🎯 功能说明 |
|------------|----------------|------------|
| 🚀 **Plug & Play** | Built-in prebuilt data, no Excel required | 内置预构建数据，无需 Excel 也可直接加载使用 |
| 📥 **Incremental Import** | Load prebuilt first, then append custom data | 支持先加载预构建数据，再增量追加自定义数据 |
| 🔄 **Full CRUD** | Complete Create/Read/Update/Delete operations | 增删改查全功能支持 |
| 📦 **JSON Export** | Export full data for Java/Web platforms | 导出全量数据供 Java、Web 等其他语言/平台使用 |
| 🌐 **Multi-format** | Time-series, text, image, audio, video data | 支持时序、文本、图像、音频、视频等多种数据类型 |
| 🛡️ **Type Safety** | Immutable dataclasses with validation | 不可变数据结构，数据验证保证类型安全 |

### 📊 Visualization Tools | 可视化工具

| 🖼️ Tool | 📁 File | 🎯 Purpose | 用途 |
|----------|---------|------------|------|
| 🌊 **Sankey Diagram** | `graph/sankey.py` | Blast furnace data pool visualization | 高炉数据池桑基图可视化 |
| 🔥 **Correlation Heatmap** | `cor_graph/cor_graph.py` | Data correlation heatmap | 数据相关性热力图 |
| 📊 **Survey Sankey** | `Questionnaire survey/` | Survey results visualization | 问卷调查数据桑基图 |

---

## 🏗️ Architecture | 系统架构

### System Architecture | 系统架构图

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    🎛️ DictionaryManager (统一管理器)                             │
│                         Unified Dictionary Manager                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐        │
│  │ BaseDict   │ CategoryDict│  PoolDict   │ DatasetDict │ AttrDict    │        │
│  │ (工种字典)  │ (类别字典)   │ (数据池字典) │ (数据集字典)  │ (属性模板)  │        │
│  └─────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴─────┬────┘        │
│        └─────────────┴─────────────┴─────────────┴─────────────┘              │
│                    ┌──────────▼──────────┐                                       │
│                    │  📋 Registry (通用注册表)  │                                │
│                    │  CRUD · JSON · Search · Duplicate Detection                │
│                    └───────────────────────┘                                    │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Core Classes | 核心类说明

| 🏷️ Class | 📁 File | 🎯 Responsibility | 职责 |
|-----------|---------|------------------|------|
| `Registry<K, T>` | `registry.py` | Generic registry with CRUD, search, JSON | 通用注册表，提供 CRUD、搜索、JSON 序列化 |
| `BaseDictionary` | `base_dictionary.py` | Work Type management | 工种字典管理 |
| `DataCategoryDictionary` | `data_category_dictionary.py` | Data category management | 数据类别字典管理 |
| `DataPoolDictionary` | `data_pool_dictionary.py` | Data pool type management | 数据池字典管理 |
| `DatasetDictionary` | `dataset_dictionary.py` | Dataset/Parameter management | 数据集/参数字典管理 |
| `DataAttributeDictionary` | `data_attribute_dictionary.py` | Attribute template management | 属性模板字典管理 |
| `DictionaryManager` | `dict_manager.py` | Unified orchestration | 统一管理器，协调所有字典 |

---

## 🚀 Quick Start | 快速开始

### 📌 Requirements | 环境要求

- 🐍 Python 3.10+
- 📦 pandas >= 1.5.0
- 📦 openpyxl >= 3.0.0

### 🔽 Installation | 安装部署

#### 方式一：Git 克隆（推荐）

```bash
# 1. 克隆项目仓库（请将 <REPO_URL> 替换为实际仓库地址）
git clone <REPO_URL>
cd <REPO_NAME>

# 2. 进入数据字典模块目录
cd Construction_data_dictionary

# 3. 安装依赖
pip install pandas openpyxl

# 4. 运行示例
python run_example.py
```

#### 方式二：直接下载 ZIP 包

```bash
# 1. 下载项目 ZIP 包并解压到本地目录（如：D:\GenBFKit）
# 2. 进入项目目录
cd D:\GenBFKit\Construction_data_dictionary

# 3. 安装依赖
pip install pandas openpyxl

# 4. 运行示例
python run_example.py
```

#### 方式三：在项目根目录创建脚本

如果需要在项目根目录（`project_image_GenBFKit/`）创建 `demo.py` 等脚本使用数据字典，请参考以下方式：

```python
# demo.py - 放在 project_image_GenBFKit/ 目录下
import sys
from pathlib import Path

# 将项目根目录添加到 sys.path，确保可以找到 Construction_data_dictionary 包
_current_file = Path(__file__).resolve()
_pkg_dir = _current_file.parent / "Construction_data_dictionary"
_project_root = _pkg_dir.parent

if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 现在可以正常导入
from Construction_data_dictionary import DictionaryManager

# 使用示例
mgr = DictionaryManager()
mgr.load_prebuilt_default()
print(mgr.get_work_types())
```

### 🎯 Basic Usage | 基本用法

```python
from pathlib import Path
from Construction_data_dictionary import DictionaryManager

# ✨ 创建管理器实例 | Create manager instance
mgr = DictionaryManager()

# 📥 加载预构建默认数据 | Load prebuilt default data
# 系统将自动加载内置的预构建数据，无需准备 Excel 文件
mgr.load_prebuilt_default()

# 🔍 获取所有工种 | Get all work types
work_types = mgr.get_work_types()
print(f"Available work types: {work_types}")
# 输出示例: ['Slag treating', 'Hot blast supplying', 'Gas & Dust treating', ...]

# 📊 获取完整数据链 | Get complete data chain
# 以第一个工种为例，获取完整的数据层级链
first_wt = work_types[0]
chain = mgr.get_full_data_chain(first_wt, include_attributes=True)

# 💾 导出为 JSON | Export to JSON
mgr.export_to_json("exported_data.json")
```

> 💡 **提示**：首次使用建议运行以下脚本查看完整示例输出：
> - `python run_example.py` - 基础使用示例
> - `python demo_import_full.py` - 完整格式导入示例（推荐）
> - `python demo_import_simple.py` - 简化模板导入示例

---

## 🔧 Advanced Usage | 高级用法

### 📊 数据导入方式总览 | Data Import Methods Overview

> 💡 **重要说明**：GenBFKit 提供 **两种数据导入模板**，分别适用于不同的使用场景。

| 导入方式 | 模板文件 | 适用场景 | 数据池类型 | 脚本文件 |
|---------|---------|---------|-----------|---------|
| **全量模板导入** | `Data_Import_Template.xlsx` | 完整定义所有层级，自定义数据池和属性 | 支持预定义9种 + 自定义类型 | `demo_import_full.py` |
| **快速模板导入** | `Data_Import_Template_Simple.xlsx` | 快速导入数据集（仅4列） | 仅支持预定义9种标准类型 | `demo_import_simple.py` |
| **Text/Image 模板** | 独立模板文件 | 导入文本/图像数据 | 固定为 Text/Image 类型 | 内置方法 |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🎯 数据导入模板选择流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1️⃣ 你是要导入什么类型的数据？                                              │
│      ├─ 仅导入数据集/参数        ──→  2️⃣                                      │
│      └─ 定义新的数据池/属性模板    ──→  使用【全量模板导入】                      │
│                                                                             │
│  2️⃣ 数据池类型是否在预定义的9种标准类型中？                                   │
│      ├─ 是（Continuous time-series, Text, Image 等）                         │
│      │   └─ 使用【快速模板导入】（简单快速，仅需4列）                            │
│      └─ 否（需要自定义新的池类型或属性）                                       │
│          └─ 使用【全量模板导入】                                              │
│                                                                             │
│  3️⃣ 是否需要导入文本/图像数据？                                             │
│      └─ 使用 Text/Image 数据模板（独立模板文件）                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 📥 方式一：全量模板导入 | Full Template Import

> **模板文件**：`templates/Data_Import_Template.xlsx`
> **脚本文件**：`demo_import_full.py`

全量模板可以一次性定义所有5个层级的数据字典，包括自定义的数据池类型和属性模板。

**模板文件结构（Sheet 1-5）：**

| Sheet | 名称 | 用途 |
|-------|------|------|
| **Sheet 1** | Base Dict (work_type) | 工种字典 - 定义业务场景 |
| **Sheet 2** | Data Category (category_dict) | 数据类别字典 - 定义系统/设备 |
| **Sheet 3** | Data Pool (Pool_dict) | 数据池字典 - 定义数据类型 |
| **Sheet 4** | Dataset Dict (Dataset_dict) | 数据集字典 - 定义具体参数 |
| **Sheet 5** | Data Attribute (Attr_dict) | 属性模板字典 - 定义字段属性 |

```python
from pathlib import Path
from Construction_data_dictionary import DictionaryManager

# 1. 创建管理器并加载预构建数据
mgr = DictionaryManager()
mgr.load_prebuilt_default()

# 2. 使用全量模板导入
counts = mgr.import_additional_data(
    Path("templates/Data_Import_Template.xlsx"),
    overwrite=False  # False=合并模式，True=覆盖模式
)

print(f"导入结果: {counts}")
# 输出示例: {'base_dictionary': 1, 'data_category_dictionary': 2, 'data_pool_dictionary': 1, 'dataset_dictionary': 10, 'data_attribute_dictionary': 5}

# 3. 导出合并后的数据
mgr.export_to_json("merged_data.json")
```

##### 📝 Full Template Format | 全量模板格式

**Sheet 1: Base Dict (work_type)**

| 列名 | 说明 | 示例 |
|------|------|------|
| Work Type | 工种英文唯一标识（使用下划线或驼峰格式） | Blast_Furnace, Slag_treating |
| Work Type 中文名 | 工种中文名称 | 高炉冶炼, 渣处理 |
| No. | 可选：顺序编号，用于排序 | 1, 2, 3 |
| 是否预构建 | 固定值：否（不可修改） | 否 |
| 备注 | 可选：附加说明 | 测试数据 |

**Sheet 2: Data Category (category_dict)**

| 列名 | 说明 | 示例 |
|------|------|------|
| Work Type | 所属工种英文标识（需与 Sheet 1 一致） | Blast_Furnace |
| Data Category | 数据类别英文唯一标识 | Process_parameters, Quality_indicators |
| Data Category 中文名 | 数据类别中文名称 | 工艺参数, 质量指标 |
| 是否预构建 | 固定值：否（不可修改） | 否 |
| 备注 | 可选：附加说明 | 测试数据 |

**Sheet 3: Data Pool (Pool_dict)**

| 列名 | 说明 | 示例 |
|------|------|------|
| Work Type | 所属工种英文标识（需与 Sheet 1 一致） | Blast_Furnace |
| Data Category | 所属数据类别英文标识（需与 Sheet 2 一致） | Process_parameters |
| Data Pool | 数据池英文标识 | Continuous_time_series_data, Custom_sensor_data |
| Data Pool 中文名 | 数据池中文名称 | 连续时序数据, 自定义传感器数据 |
| 是否预构建 | 固定值：否（不可修改） | 否 |
| 备注 | 可选：附加说明 | 测试数据 |

> ⚠️ **注意**：Data Pool 可以使用预定义的9种标准类型（如 `Continuous_time_series_data`），也可以自定义新的池类型。

**Sheet 4: Dataset Dict (Dataset_dict)**

| 列名 | 说明 | 示例 |
|------|------|------|
| Work Type | 所属工种英文标识（需与 Sheet 1 一致） | Blast_Furnace |
| Data Category | 所属数据类别英文标识（需与 Sheet 2 一致） | Process_parameters |
| Data Pool | 数据池英文标识（需与 Sheet 3 一致） | Continuous_time_series_data |
| Dataset | 数据集英文唯一标识（建议使用有意义的英文名称） | Blast_pressure, Hot_metal_temp |
| Dataset 中文名 | 数据集中文名称 | 高炉压力, 铁水温度 |
| Dataset 简称 | 可选：数据集简称 | 炉压, 铁温 |
| 备注 | 可选：附加说明 | 测试数据 |

**Sheet 5: Data Attribute (Attr_dict)**

| 列名 | 说明 | 示例 |
|------|------|------|
| Data Pool | 数据池英文标识（需与 Sheet 3 一致） | Continuous_time_series_data |
| Attribute ID | 属性标识符（建议使用格式：attribute_1, attribute_2...） | attribute_1, attribute_2 |
| Attribute Name | 属性名称（英文）★ | max_value, unit, description |
| Attribute Name 中文 | 属性中文名称（仅供参考） | 最大值, 单位, 描述 |
| Attribute Description | 属性描述（可选） | 说明该属性的含义 |
| 备注 | 可选：附加说明 | 测试数据 |

> ★ **注意**：`Attribute Name` 列的英文内容将作为属性值被导入系统，`Attribute Name 中文` 列仅供中文参考，不影响导入结果。该列可以对新增 data pool进行属性定义，但不可对预构建的9中 data pool进行修改。 

> ⚠️ **注意**：属性模板定义了不同数据池类型的字段结构，是数据库建表的核心依据。

#### 📋 方式二：快速模板导入 | Simple Template Import

> **模板文件**：`templates/Data_Import_Template_Simple.xlsx`

快速模板用于快速导入数据集，只需 4 列数据。系统会自动创建关联的工种和数据类别。

> 💡 **提示**：使用快速模板导入时，新增的工种序号会自动递增填写（从当前最大序号开始，★ 推荐），也可手动填写序号，但手动填写需要保证填写正确。

```python
from pathlib import Path
from Construction_data_dictionary import DictionaryManager

# 1. 创建管理器并加载预构建数据
mgr = DictionaryManager()
mgr.load_prebuilt_default()

# 2. 使用快速模板导入
result = mgr.import_from_simple_template(
    Path("templates/Data_Import_Template_Simple.xlsx"),
    work_type_zh="",  # 可选：工种中文名
    category_zh="",    # 可选：类别中文名
    overwrite=False
)
print(result)
# 输出示例: {'work_types_added': 1, 'categories_added': 2, 'datasets_added': 2, 'rows_skipped': 1}

# 3. 导出更新后的数据
mgr.export_to_json("updated_data.json")
```

##### 📝 Simple Template Format | 简化模板格式

> ⚠️ **模板文件结构说明** (Sheet 1)：
> - 第1行：标题
> - 第2行：使用说明
> - 第3行：**列头** (Work Type, Data Category, Data Pool, Dataset)
> - 第4行：列说明（系统自动跳过）
> - 第5行起：数据行

| 📌 Column | 📝 Description | 说明 | 🎯 Example |
|-----------|----------------|------|------------|
| `Work Type` | Work type (English) | 工种英文标识 | Blast_Furnace |
| `Data Category` | Data category (English) | 数据类别英文标识 | Process_parameters |
| `Data Pool` | Data pool type (9 types) | 数据池类型（支持带下划线格式） | Continuous_time_series_data |
| `Dataset` | Dataset/Parameter name | 数据集/参数名称 | Blast_pressure |

> ⚠️ **重要**：
> - Data Pool 必须是预构建的 9 种标准池类型之一，**支持带下划线格式**（如 `Continuous_time_series_data`）
> - 系统会自动将下划线格式转换为标准格式（如 `Continuous time-series data`）
> - 不可自定义新增池类型
> - 可在 **Data Pool** 表单中查看所有标准池类型

> 📋 **支持的 Data Pool 类型**（9种）：
> | 模板格式（带下划线） | 标准格式（带空格） |
> |---------------------|-------------------|
> | Continuous_time_series_data | Continuous time-series data |
> | Discrete_time_series_data | Discrete time-series data |
> | Batch_time_series_data | Batch time-series data |
> | Text_data | Text data |
> | Image_data | Image data |
> | Binary_status_data | Binary status data |
> | Controllable_data | Controllable data |
> | Constraint_data | Constraint data |
> | Response_data | Response data |

#### 🖼️ Text / Image Data Templates | 文本/图像数据模板

> ⚠️ **重要说明**：
> - **预构建属性**：这些属性存储在 `data_attribute_dictionary` 中，定义了每个数据池类型的标准字段，是预构建数据架构的核心组成部分，**不可更改**。
> - **扩展属性**：以下模板中的其他字段（如 Data Source、Annotation Status 等）是基于预构建属性的**扩展字段**，用于完善数据管理功能。这些扩展字段**不影响预构建数据架构**，但会**影响数据库表的最终建表结构**。

```python
# 📝 导入 Text data 模板 | Import Text data template
result_text = mgr.import_text_data_template(
    Path("templates/text_data_template.xlsx"),
    overwrite=False
)
print(f"Text data: {result_text['datasets_added']} datasets added")

# 🖼️ 导入 Image data 模板 | Import Image data template
result_image = mgr.import_image_data_template(
    Path("templates/image_data_template.xlsx"),
    overwrite=False
)
print(f"Image data: {result_image['datasets_added']} datasets added")
```

##### 📝 Text Data Template Format | 文本数据模板格式

> **模板文件**：`templates/text_data_template.xlsx` → Sheet: `Text data storage`
> **属性参考**：`templates/text_data_template.xlsx` → Sheet: `Text Attributes Reference`

**一、预构建数据架构中的标准属性（必须与预构建一致）**

| 📌 Column | 📝 Description | 说明 | 🎯 Example |
|-----------|----------------|------|------------|
| `English Name` ★ | Parameter English name | 参数英文名（作为数据库字段名） | Daily_production_log |
| `Chinese Name` ★ | Parameter Chinese name | 参数中文名 | 每日生产日志 |
| `Data Storage Type` ★ | Database storage type | 数据库存储类型 | LONGTEXT |
| `Text Encoding` ★ | Text encoding | 文本编码格式 | UTF-8 |
| `Text Format` ★ | Text format | 文本格式 | JSON |
| `Max Length` ★ | Max character limit | 最大字符数 | 50000 |
| `Min Length` ★ | Min character limit | 最小字符数 | 100 |
| `Keyword Set` | Keywords (comma-separated) | 关键词集合 | 产量,质量,设备状态 |
| `Annotation Label` | Annotation labels | 标注标签 | 正常,异常 |

**二、扩展属性（影响数据库建表但不影响预构建架构）**

| 📌 Column | 📝 Description | 说明 | 🎯 Example |
|-----------|----------------|------|------------|
| `Work Type` | Work type (English) | 工种（系统自动关联） | Blast_Furnace |
| `Data Category` | Data category (English) | 数据分类（系统自动关联） | Production_report |
| `Dataset ID` ★ | Unique identifier | 唯一标识符 | TXT_BF_001 |
| `Data Pool` | Fixed: Text data | 数据池类型（固定值） | Text data |
| `Data Description` | Data description | 数据描述 | 高炉每日生产运行日志 |
| `Data Source` | Data source | 数据来源 | 生产管理系统自动生成 |
| `Language` | Text language | 文本语言 | 中文 |
| `Content Template` | Content template | 内容模板 | JSON结构模板 |
| `Structured Fields` | Structured fields | 结构化字段定义 | date,shift,output |
| `Priority Level` | Priority (1=highest, 5=lowest) | 优先级 | 2 |
| `Creation Time` | Creation time | 创建时间 | 2025-01-15 |
| `Annotation Status` | Annotation status | 标注状态 | 已完成 |
| `Text Content` | Sample text content | 样本文本内容 | JSON格式示例 |
| `File Path` | External file path | 外部文本文件路径 | D:/texts/log.json |
| `Remarks` | Additional remarks | 备注信息 | 测试数据样例 |
| `Last Updated` | Last updated time | 最后更新时间 | 2025-01-20 10:30:00 |

**三、预构建属性参考（Text Attributes Reference）**

| Attribute ID | Attribute Name (EN) | Attribute Name (CN) | Description |
|--------------|---------------------|-------------------|-------------|
| attribute_1 | English_name | 英文名称 | 记录该数据对应的英文命名 |
| attribute_2 | Chinese_name | 中文名称 | 记录该数据对应的中文命名 |
| attribute_3 | Data_storage_type | 数据存储类型 | 说明数据在数据库中的存储类型 |
| attribute_4 | Storage_location | 数据存储位置 | 指明数据文件或记录的存储路径 |
| attribute_5 | Data_description | 数据描述 | 对数据含义、用途及内容进行简要说明 |
| attribute_6 | Priority_level | 优先级 | 表示该数据项的重要程度等级 |
| attribute_7 | Creation_time | 创建时间 | 记录该数据生成的时间点 |
| attribute_8 | Text_encoding | 文本编码 | 文本编码格式 |
| attribute_9 | Max_length | 最大长度 | 文本最大字符数限制 |
| attribute_10 | Min_length | 最小长度 | 文本最小字符数要求 |
| attribute_11 | Text_format | 文本格式 | 文本格式类型 |
| attribute_12 | Keyword_set | 关键词集合 | 用于文本检索的关键词 |
| attribute_13 | Annotation_label | 标注标签 | 用于标注本条文本数据的额外标签 |

##### 🖼️ Image Data Template Format | 图像数据模板格式

> **模板文件**：`templates/image_data_template.xlsx` → Sheet: `Image data storage`
> **属性参考**：`templates/image_data_template.xlsx` → Sheet: `Image Attributes Reference`

**一、预构建数据架构中的标准属性（必须与预构建一致）**

| 📌 Column | 📝 Description | 说明 | 🎯 Example |
|-----------|----------------|------|------------|
| `English Name` ★ | Parameter English name | 参数英文名（作为数据库字段名） | BF_Top_combustion_image |
| `Chinese Name` ★ | Parameter Chinese name | 参数中文名 | 高炉炉顶燃烧状态图像 |
| `Storage Type` ★ | Database storage type | 数据库存储类型 | 文件路径 |
| `Image Format` ★ | Image format | 图像格式 | JPEG |
| `Color Mode` ★ | Color mode | 色彩模式 | RGB |
| `Resolution` ★ | Image resolution | 图像分辨率 | 1920x1080 |

**二、扩展属性（影响数据库建表但不影响预构建架构）**

| 📌 Column | 📝 Description | 说明 | 🎯 Example |
|-----------|----------------|------|------------|
| `Work Type` | Work type (English) | 工种（系统自动关联） | Blast_Furnace |
| `Data Category` | Data category (English) | 数据分类（系统自动关联） | Equipment_inspection |
| `Dataset ID` ★ | Unique identifier | 唯一标识符 | IMG_BF_001 |
| `Data Pool` | Fixed: Image data | 数据池类型（固定值） | Image data |
| `Data Description` | Data description | 数据描述 | 高炉炉顶区域设备运行状态监测图像 |
| `Data Source` | Data source | 数据来源 | 现场工业摄像头 |
| `Image Quality` | Image quality | 图像质量 | 高质量(95%) |
| `File Size Limit (MB)` | File size limit | 单文件大小上限(MB) | 20 |
| `Blur Threshold` | Blur detection threshold | 模糊检测阈值 | 0.3 |
| `Priority Level` | Priority (1=highest, 5=lowest) | 优先级 | 2 |
| `Creation Time` | Creation time | 创建时间 | 2025-01-15 |
| `Annotation Type` | Annotation type | 标注类型 | Classification |
| `Label Name` | Label name | 标注标签 | Normal,Abnormal,Wear |
| `Annotation Status` | Annotation status | 标注状态 | 已完成 |
| `Image Path` | Image file path | 图像文件路径 | D:/images/bf_001.jpg |
| `Image Base64` | Image in Base64 | Base64格式图像 | (Base64 string) |
| `Remarks` | Additional remarks | 备注信息 | 测试数据样例 |
| `Last Updated` | Last updated time | 最后更新时间 | 2025-01-20 10:30:00 |

**三、预构建属性参考（Image Attributes Reference）**

| Attribute ID | Attribute Name (EN) | Attribute Name (CN) | Description |
|--------------|---------------------|-------------------|-------------|
| attribute_1 | English_name | 英文名称 | 记录该数据对应的英文命名 |
| attribute_2 | Chinese_name | 中文名称 | 记录该数据对应的中文命名 |
| attribute_3 | Data_storage_type | 数据存储类型 | 说明数据在数据库中的存储类型 |
| attribute_4 | Storage_location | 数据存储位置 | 指明数据文件或记录的存储路径 |
| attribute_5 | Data_description | 数据描述 | 对数据含义、用途及内容进行简要说明 |
| attribute_6 | Priority_level | 优先级 | 表示该数据项的重要程度等级 |
| attribute_7 | Creation_time | 创建时间 | 记录该数据生成的时间点 |
| attribute_8 | Image_resolution | 图像分辨率 | 描述图像的像素尺寸与清晰度规格 |
| attribute_9 | Image_format | 图像格式 | 指明图像文件的存储格式类型 |
| attribute_10 | Color_mode | 色彩模式 | 表示图像采用的色彩空间模式 |
| attribute_11 | Blur_threshold | 模糊阈值 | 判定图像是否模糊的临界参数值 |
| attribute_12 | Annotation_type | 标注类型 | 说明图像数据采用的标注方式与类别 |

---

## 📊 Data Model | 数据模型

### 🧑‍🏭 Work Types | 工种列表

> ⚠️ **注意**：工种按预构建数据中的编号（No.）排序。

| 🇬🇧 English | 🇨🇳 中文 | 📝 No. | 📝 Description |
|-------------|---------|------|----------------|
| Slag treating | 渣处理 | No.1 | Slag treatment |
| Hot blast supplying | 热风供给 | No.2 | Hot blast supply |
| Gas & Dust treating | 煤气处理 | No.3 | Gas & dust treatment |
| Equipment maintaining | 设备维护 | No.4 | Equipment maintenance |
| Cooling monitoring | 冷却监测 | No.5 | Cooling system monitoring |
| Burden feeding | 布料监控 | No.6 | Burden feeding monitoring |
| BF tapping | 出铁作业 | No.7 | Blast furnace tapping |
| BF operating | 高炉操作 | No.8 | Blast furnace operation |

### 🗃️ Data Pool Types | 数据池类型

> ⚠️ **注意**：以下 9 类数据类型模板与预构建数据完全一致，用于规范每个数据集的存储类型。
> **这些池类型不可更改**，但可在预构建基础上扩展新的数据集条目。

| 🗃️ Pool Type | 🇨🇳 中文说明 | 📝 Description |
|-------------|-------------|----------------|
| Continuous time-series data | 连续时序数据 | Sensor readings, continuous measurements (传感器读数、连续测量) |
| Discrete time-series data | 离散时序数据 | Discrete or batch measurements (离散或批量测量) |
| Text data | 文本数据 | Logs, reports, notes (日志、报告、注释) |
| Binary status data | 二值状态数据 | On/Off, Open/Close states (开关状态) |
| Controllable data | 可控数据 | Controllable parameters (可控工艺参数) |
| Constraint data | 约束数据 | Constraint boundaries (约束边界条件) |
| Batch time-series data | 批量时序数据 | Batch/process time-series (批次/过程时序) |
| Image data | 图像数据 | Photos, screenshots, camera images (照片、截图、摄像图像) |
| Response data | 响应数据 | System response outputs (系统响应输出) |

### 📈 Data Statistics | 数据统计

| 📊 Level | 🔢 Count | 说明 |
|----------|---------|------|
| Work Types | 8 | 工种数量 |
| Data Categories | 98 | 数据类别数量 |
| Data Pools | 9 | 数据池类型数量 |
| Datasets | 2128 | 数据集/参数数量 |

---

## 📚 API Reference | API 参考

### DictionaryManager

> ⚠️ **注意**：`import_additional_data` 方法会查找 Excel 文件所在目录中的字典文件。请参考快速开始中的说明。

| 📌 Method | 🎯 Description | 说明 |
|----------|----------------|------|
| `load_from_project_root(path, overwrite=True)` | Load from project root | 从项目根目录加载数据 |
| `load_prebuilt_default(overwrite=True)` | Load prebuilt data | 加载预构建数据 |
| `import_additional_data(excel_path, overwrite=False)` | Incremental import | 增量导入额外数据（合并模式） |
| `import_from_simple_template(excel_path, ...)` | Simple template import | 从简化 4 列模板导入 |
| `import_text_data_template(excel_path, overwrite=False)` | Text data template import | 从 Text data 模板导入 |
| `import_image_data_template(excel_path, overwrite=False)` | Image data template import | 从 Image data 模板导入 |
| `load_text_data_template(excel_path)` | Load Text data template | 读取 Text data 模板为 DataFrame |
| `load_image_data_template(excel_path)` | Load Image data template | 读取 Image data 模板为 DataFrame |
| `export_to_json(output_path, include_all=True)` | Export to JSON | 导出为 JSON |
| `get_work_types()` | Get all work types | 获取所有工种列表 |
| `get_full_data_chain(work_type, include_attributes=True)` | Get complete data chain | 获取完整数据链 |
| `get_pool_attributes(pool_type)` | Get pool attributes | 获取指定池类型的属性模板 |

### Individual Dictionary Classes | 各字典类通用方法

| 📌 Method | 🎯 Description | 说明 |
|----------|----------------|------|
| `add(...)` | Add new record | 添加新记录 |
| `get(...)` | Get single record | 获取单条记录 |
| `update(...)` / `delete(...)` | Update / Delete record | 更新 / 删除记录 |
| `list_all()` | List all records | 获取所有记录 |
| `exists(...)` | Check if exists | 检查记录是否存在 |
| `save_json(path)` | Save to JSON | 保存为 JSON |
| `load_from_excel(path)` | Load from Excel | 从 Excel 加载 |

---

## 🗄️ Database Builder | 数据库构建模块

> 💡 **新功能**：GenBFKit 提供完整的数据库构建功能，支持将导出的 JSON 数据全量构建为 PostgreSQL 数据库物理表。

### 📋 功能概述

| 功能 | 说明 |
|------|------|
| **元数据管理** | 存储 5 层数据层级结构（工种→类别→数据池→数据集→属性） |
| **中文回填** | JSON 导入时自动从 lookup 表补全 work_type_zh / category_zh / pool_zh；支持 `--backfill` 修复已入库记录 |
| **幂等增量导入** | 重复导入幂等去重；自动检测新增数据集和属性变更 |
| **自适应建表** | 新增数据集自动建表；已有池类型属性变更自动重建相关物理表；支持自定义新池类型 |
| **动态表构建** | 根据数据池类型的属性模板，为每个 Dataset 创建独立的物理表 |
| **Web API** | FastAPI 接口提供数据管理功能 |
| **可视化界面** | HTML Dashboard 展示数据库状态（统计概览/表列表/Schema/树形结构） |
| **SQL 导出** | 导出建表 SQL 脚本 |

### 🛠️ 技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| **数据库** | PostgreSQL | 工业级可靠性、JSON 支持、复杂查询强 |
| **ORM 框架** | SQLAlchemy 2.0 | Python 最成熟 ORM、类型安全 |
| **Web 框架** | FastAPI | 现代高性能、自动 API 文档 |
| **前端** | 原生 HTML/CSS/JS | 零依赖、轻量级部署 |

### 🔧 环境要求

> **本模块依赖 PostgreSQL 数据库**，请在继续之前确保已完成以下准备工作。

#### 📦 安装 PostgreSQL

**Windows：**

1. 下载 [PostgreSQL 安装包](https://www.postgresql.org/download/windows/)（推荐使用 [EnterpriseDB 安装器](https://www.postgresql.org/download/windows/)）
2. 安装时记住设置的 `postgres` 用户密码
3. 默认端口 `5432`，安装完成后可在 `pgAdmin` 或 `psql` 中验证

**macOS：**

```bash
brew install postgresql
brew services start postgresql   # 启动服务
```

**Ubuntu / Debian：**

```bash
sudo apt update && sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql  # 启动服务
```

#### ⚙️ 创建数据库

连接 PostgreSQL 后，执行以下命令创建数据库：

```sql
-- 以 postgres 超级用户身份进入 psql
sudo -u postgres psql

-- 创建数据库（如已存在可跳过）
CREATE DATABASE genbfkit;

-- 创建专用用户（可选，推荐）
CREATE USER genbfkit_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE genbfkit TO genbfkit_user;

-- 将数据库 owner 设为新用户
ALTER DATABASE genbfkit OWNER TO genbfkit_user;
```

#### 🔐 配置数据库连接

```bash
# 1. 复制环境变量示例文件
cp db_builder/.env.example db_builder/.env

# 2. 编辑 .env 文件，修改以下配置项
#    GENBFKIT__DATABASE__HOST       = localhost
#    GENBFKIT__DATABASE__PORT       = 5432
#    GENBFKIT__DATABASE__DATABASE   = genbfkit
#    GENBFKIT__DATABASE__USERNAME   = postgres（或自定义用户名）
#    GENBFKIT__DATABASE__PASSWORD   = your_password
```

> **安全提示**：生产环境中请务必修改默认密码，避免使用 `postgres` 超级用户直接连接应用，推荐使用专用数据库用户。

#### 📦 安装 Python 依赖

```bash
# 进入项目目录
cd Construction_data_dictionary

# 安装依赖（推荐使用虚拟环境）
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r db_builder/requirements.txt
```

### 🚀 快速开始

#### 方式一：使用命令行脚本

```bash
# 1. 进入项目目录
cd Construction_data_dictionary

# 2. 安装依赖
pip install -r db_builder/requirements.txt

# 3. 配置数据库连接（修改 .env 文件）
cp db_builder/.env.example db_builder/.env
# 编辑 .env 填入数据库密码等配置

# 4. 初始化数据库（元数据表 + JSON 数据导入）
python db_builder/scripts/init_db.py

# 5. 回填缺失的中文列（如 work_type_zh / category_zh / pool_zh）
python db_builder/scripts/build_tables.py --backfill

# 6. 从 JSON 构建所有物理数据表
python db_builder/scripts/build_tables.py --json prebuilt_full.json

# 7. 查看示例
python db_builder/scripts/demo.py
```

#### 方式二：使用 Web 可视化界面

```bash
# 1. 启动 FastAPI 服务
cd Construction_data_dictionary
uvicorn db_builder.api.main:app --reload --host 0.0.0.0 --port 8000

# 2. 打开浏览器访问
#    - Dashboard: http://localhost:8000
#    - API 文档: http://localhost:8000/api/docs
#    - ReDoc: http://localhost:8000/api/redoc
```

#### 方式三：Python 代码使用

```python
from pathlib import Path
from db_builder.services.database_manager import DatabaseManager
from db_builder.config import DatabaseSettings

# 配置数据库连接
db_settings = DatabaseSettings(
    host="localhost",
    port=5432,
    database="genbfkit",
    username="postgres",
    password="your_password",
)

# JSON 数据文件路径
json_path = Path("prebuilt_full.json")

# 初始化管理器
manager = DatabaseManager(db_settings=db_settings, json_path=json_path)

# 1. 初始化数据库（元数据表 + JSON 数据导入）
manager.initialize_database()

# 2. 回填缺失的中文列（work_type_zh / category_zh / pool_zh）
backfill_stats = manager.backfill_chinese_columns()
print(f"回填: {backfill_stats}")

# 3. 构建所有物理表
result = manager.build_tables(overwrite=False)

# 4. 获取统计信息
stats = manager.get_statistics()
print(f"工种: {stats.total_work_types}")
print(f"数据集: {stats.total_datasets}")
print(f"物理表: {stats.total_tables}")
print(f"数据库大小: {stats.database_size_mb} MB")
```

### 📊 数据池类型与表结构

每个 Dataset 对应一张物理表，表结构由其所属 Data Pool 类型决定：

| 数据池类型 | 中文名 | 标准列 |
|-----------|--------|--------|
| Continuous time-series data | 连续时序数据 | dataset_id, timestamp, value, unit, max_value, min_value, quality |
| Discrete time-series data | 离散时序数据 | dataset_id, timestamp, value, quality |
| Batch time-series data | 批量时序数据 | dataset_id, batch_id, timestamp, value, unit, quality |
| Binary status data | 二元状态数据 | dataset_id, timestamp, status, duration_seconds, quality |
| Text data | 文本数据 | dataset_id, timestamp, content, encoding, format, keywords |
| Image data | 图像数据 | dataset_id, timestamp, image_path, format, resolution, labels |
| Controllable data | 可控数据 | dataset_id, timestamp, set_value, actual_value, status, quality |
| Constraint data | 约束数据 | dataset_id, timestamp, value, min_value, max_value, status |
| Response data | 响应数据 | dataset_id, timestamp, input_value, output_value, delay_seconds |

### 🔄 增量导入与自适应建表

> **核心能力**：GenBFKit 支持增量 JSON 导入，自动检测新增数据集和属性变更，一体化完成元数据同步与物理表自适应重建，无需手动干预。

#### 🔍 自适应场景说明

| 场景 | 系统行为 | 是否支持 |
|------|---------|---------|
| 新增数据集（已有池类型） | 自动为新增数据集构建物理表 | ✅ 支持 |
| 新增数据池类型（自定义属性） | 自动注册属性模板 + 为所有相关数据集重建物理表 | ✅ 支持 |
| 修改已有池类型的属性 | 自动检测属性差异 + 为该池类型下所有数据集重建物理表 | ✅ 支持 |
| 重复导入相同数据 | 幂等去重，不重复插入 | ✅ 支持 |
| 删除数据集 | 需手动处理（保留幂等设计，数据安全优先） | ⚠️ 需扩展 |

#### 🚀 增量导入方式

**方式一：命令行（推荐）**

```bash
# 增量导入：自动检测新增数据集 + 属性变更，一体化完成
python db_builder/scripts/build_tables.py --incremental --json prebuilt_full.json
```

**方式二：Web API**

```bash
# 增量导入（POST 请求）
curl -X POST "http://localhost:8000/api/incremental-import?json_path=prebuilt_full.json"
```

**方式三：Python 代码**

```python
from pathlib import Path
from db_builder.services.database_manager import DatabaseManager
from db_builder.config import DatabaseSettings

manager = DatabaseManager(
    db_settings=DatabaseSettings(password="your_password"),
    json_path=Path("prebuilt_full.json")
)

# 一体化增量导入（自动完成：元数据同步 → 新增表构建 → 属性变更重建）
result = manager.incremental_import(Path("prebuilt_full.json"))

print(f"新增数据集: {result['import_stats']['datasets']}")
print(f"新建物理表: {result.get('build_response', {}).get('tables_created', 0)}")
print(f"重建池类型: {result['rebuild_pool_types']}")
# 示例输出:
# 新增数据集: 10
# 新建物理表: 10
# 重建池类型: ['Custom sensor data']
```

#### ⚙️ 自适应建表原理

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    增量导入自适应建表流程                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ① JSON 数据加载                                                            │
│     └─→ 比对已有元数据，检测新增项和变更项                                      │
│                                                                             │
│  ② 元数据同步（幂等 Upsert）                                                  │
│     ├─ 新增工种/类别/数据池/数据集 → 幂等插入                                   │
│     ├─ 属性模板：不存在 → 新增；已存在且属性变化 → 更新                            │
│     └─ 标记 rebuild_pool_types（属性变更的池类型列表）                            │
│                                                                             │
│  ③ 新增数据集建表（table_created='pending' 的）                                │
│     └─ 按各数据集所属池类型加载属性模板 → 创建物理表                               │
│                                                                             │
│  ④ 属性变更池类型重建（如有）                                                   │
│     └─ 删除旧物理表 → 按最新属性模板重建 → 更新 meta_datasets.table_created        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **属性变更影响范围**：当某个池类型的属性被修改时，该池类型下**所有数据集对应的物理表**均会被重建（删除旧表 → 按新属性创建），请注意备份已有数据。

#### 🛠️ 单独重建指定池类型的物理表

若仅需强制重建某个池类型的物理表（例如属性调整后手动触发），可使用：

```python
# Python API：重建指定池类型的所有物理表
result = manager.rebuild_pool_tables(["Continuous time-series data", "Custom sensor data"])
print(f"重建了 {result.tables_created} 张表")
```

### 🌐 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/connection` | GET | 获取数据库连接信息 |
| `/api/init` | POST | 初始化数据库（创建元数据表并导入 JSON 数据） |
| `/api/build` | POST | 从 JSON 文件构建物理数据表（默认跳过已存在的表） |
| `/api/incremental-import` | POST | **增量导入**：自动检测新增数据集 + 属性变更，一体化完成 |
| `/api/full-build` | POST | 一体化构建：初始化 + 增量导入 + 自适应建表（推荐） |
| `/api/rebuild-pool` | POST | 重建指定数据池类型的所有物理表（属性模板变更后使用） |
| `/api/backfill` | POST | 回填 meta_datasets 中缺失的中文列 |
| `/api/stats` | GET | 获取数据库统计信息（工种/类别/池/数据集/表数量、数据库大小等） |
| `/api/stats/schema` | GET | 获取统计信息的前端展示 Schema |
| `/api/tables` | GET | 列出所有物理数据表（支持按数据池类型/工种过滤） |
| `/api/tables/{name}` | GET | 获取指定表的详细信息（含列定义和建表 SQL） |
| `/api/tables/{name}/sql` | GET | 获取指定表的建表 SQL 语句 |
| `/api/tree` | GET | 获取数据集树形结构（工种→类别→数据池→数据集层级） |
| `/api/schemas/pool-types` | GET | 获取所有 9 种数据池类型的 Schema 定义 |
| `/api/schemas/pool-types/{type}` | GET | 获取指定数据池类型的 Schema |
| `/api/export/sql` | POST | 导出完整建表 SQL 脚本到文件 |

### 📁 db_builder 目录结构

```
db_builder/                           # 🗄️ 数据库构建模块
├── __init__.py                      # 包入口，导出公共 API
├── config.py                        # 配置（数据库连接、环境变量等）
├── requirements.txt                 # Python 依赖包
├── .env.example                     # 环境变量示例文件
│
├── models/                          # 📊 ORM 模型
│   ├── __init__.py
│   ├── base.py                      # SQLAlchemy 基类和混入
│   ├── metadata.py                   # 元数据表模型（工种、类别、数据池、数据集、属性模板）
│   └── dynamic_tables.py             # 动态表模型生成器
│
├── schemas/                         # 📝 Pydantic Schemas
│   ├── __init__.py
│   └── database.py                  # 数据库相关 Schema 定义
│
├── services/                        # ⚙️ 业务逻辑
│   ├── __init__.py
│   ├── table_builder.py             # 表构建服务（核心）
│   ├── schema_generator.py          # Schema 生成器
│   └── database_manager.py           # 数据库管理器（统一接口）
│
├── api/                             # 🌐 FastAPI 接口
│   ├── __init__.py
│   ├── main.py                      # FastAPI 主应用
│   └── routes.py                    # API 路由定义
│
├── web/                             # 🖥️ Web 可视化
│   └── index.html                   # Dashboard 页面
│
└── scripts/                         # 📜 命令行脚本
    ├── init_db.py                   # 数据库初始化
    ├── build_tables.py              # 全量构建表
    └── demo.py                      # 使用示例
```

### 🔄 数据库构建工作流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        数据库构建完整工作流程                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1️⃣ 导出 JSON 数据                                                         │
│     └─→ DictionaryManager.export_to_json("prebuilt_full.json")              │
│                                                                             │
│  2️⃣ 安装依赖                                                               │
│     └─→ pip install -r db_builder/requirements.txt                         │
│                                                                             │
│  3️⃣ 配置数据库连接                                                         │
│     └─→ 复制 .env.example 为 .env，修改数据库配置                             │
│                                                                             │
│  4️⃣ 初始化数据库（元数据表 + JSON 数据导入）                                   │
│     └─→ python db_builder/scripts/init_db.py                                │
│         或: POST /api/init                                                  │
│                                                                             │
│  5️⃣ 回填缺失的中文列                                                        │
│     └─→ python db_builder/scripts/build_tables.py --backfill                │
│         （自动从 meta_work_types / meta_data_categories /                   │
│          meta_data_pools 补全 work_type_zh / category_zh / pool_zh）        │
│                                                                             │
│  6️⃣ 一体化构建（推荐，一行命令搞定）                                          │
│     └─→ python db_builder/scripts/build_tables.py --full --json prebuilt_full.json
│         或: POST /api/full-build                                           │
│         自动完成：初始化元数据表 → 增量导入 → 自适应建表                        │
│                                                                             │
│  6️⃣ 构建物理数据表（增量模式，已初始化后的增量更新）                            │
│     └─→ python db_builder/scripts/build_tables.py --incremental              │
│                --json prebuilt_full.json                                    │
│         或: POST /api/incremental-import                                    │
│         自动检测：新增数据集 → 自动建表                                        │
│                   已有池类型属性变更 → 自动重建相关物理表                        │
│                   新增池类型 → 自动注册模板 + 重建相关物理表                      │
│                                                                             │
│  7️⃣ 查看结果（Web 界面）                                                    │
│     └─→ uvicorn db_builder.api.main:app --reload                           │
│         访问 http://localhost:8000                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

> 💡 **推荐使用一体化构建（`--full`）**，一次命令自动完成所有步骤（初始化 + 增量导入 + 自适应建表），无需分步执行。

### ⌨️ 命令行工具参考

#### `build_tables.py` — 表构建脚本

```bash
python db_builder/scripts/build_tables.py [OPTIONS]

# 常用选项：
#   -j, --json PATH      指定 JSON 数据文件路径（默认: prebuilt_full.json）
#   -f, --full           一体化构建（推荐）：自动完成初始化 + 增量导入 + 自适应建表
#   -i, --incremental    增量导入模式：自动检测新增数据集和属性变更
#   -o, --overwrite      覆盖已存在的物理表（与 --incremental 配合时覆盖所有表）
#   -b, --backfill       仅回填 meta_datasets 中缺失的中文列（不重建表）
#   -h, --host           数据库主机（默认: localhost）
#   -p, --port           数据库端口（默认: 5432）
#   -d, --database       数据库名（默认: genbfkit）
#   -u, --username       用户名（默认: postgres）
#   -w, --password       密码（可从环境变量 GENBFKIT__DATABASE__PASSWORD 读取）
```

**使用示例：**

```bash
# 【推荐】一体化构建：自动完成初始化 + 增量导入 + 自适应建表
python db_builder/scripts/build_tables.py --full --json prebuilt_full.json

# 增量导入（已有数据库，仅更新新增数据和属性变更）
python db_builder/scripts/build_tables.py --incremental --json prebuilt_full.json

# 全量重建：覆盖所有物理表（慎用，会丢失数据）
python db_builder/scripts/build_tables.py --json prebuilt_full.json --overwrite

# 仅回填中文列（已建表后修复）
python db_builder/scripts/build_tables.py --backfill

# 指定数据库连接
python db_builder/scripts/build_tables.py --host 192.168.1.100 -p 5432 -d genbfkit -u postgres -w mypassword --json prebuilt_full.json --full
```

#### `init_db.py` — 数据库初始化脚本

```bash
python db_builder/scripts/init_db.py [OPTIONS]

# 常用选项：
#   -j, --json PATH      JSON 数据文件路径（默认: prebuilt_full.json）
#   --skip-import        仅创建元数据表（不导入 JSON 数据）
#   -h, --host           数据库主机（默认: localhost）
#   -p, --port           数据库端口（默认: 5432）
#   -d, --database       数据库名（默认: genbfkit）
#   -u, --username       用户名（默认: postgres）
```

### 📋 数据库表结构说明

#### 元数据表（存储数据字典层级结构）

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| `meta_work_types` | 工种元数据 | id, work_type_en, work_type_zh, no |
| `meta_data_categories` | 数据类别元数据 | id, work_type_en, work_type_zh, category_en, category_zh |
| `meta_data_pools` | 数据池元数据 | id, work_type_en, work_type_zh, category_en, category_zh, pool_en, pool_zh |
| `meta_datasets` | 数据集元数据 | id, work_type_en, work_type_zh, category_en, category_zh, pool_en, pool_zh, dataset_en, dataset_zh, dataset_zh_short, physical_table_name, table_name, table_created |
| `meta_attribute_templates` | 属性模板元数据 | id, pool_type, attributes (JSONB) |

> **说明**：`meta_datasets` 表中 `work_type_zh` / `category_zh` / `pool_zh` 字段在 JSON 导入时**自动从对应 lookup 表补全**，若 JSON 中缺失则由系统自动回填，无需手动维护。

#### 物理数据表（每个 Dataset 对应一张表）

- 表名格式: `{work_type}_{category}_{pool}_{dataset}`（全小写，下划线分隔）
- 包含列: `id`, `dataset_id`, `created_at`, 以及根据数据池类型的业务列

---

## 📂 File Structure | 文件结构

```
Construction_data_dictionary/          # 🔧 核心数据字典包
│
├── __init__.py                     # 📦 包入口，导出公共 API
│
├── README.md                       # 📖 项目文档
│
├── run_example.py                  # 🎯 使用示例脚本
│
├── demo_import_full.py             # 📥 完整字典格式导入示例（Sheet 1-5）
│
├── demo_import_simple.py           # 📋 简化模板导入示例（Sheet 6）
│
├── export_full_data.py             # 💾 全量数据导出脚本
│
├── core/                          # 🔧 核心模块
│   ├── __init__.py                # 核心模块入口
│   ├── dict_manager.py            # 🎛️ 统一管理器 (GenBFKitDictManager)
│   ├── prebuilt_default.py       # 📦 预构建数据 (Base64 压缩存储)
│   │
│   └── dictionary/               # 📋 核心字典模块
│       ├── __init__.py
│       ├── registry.py          # 🔧 通用注册表 (CRUD 基类)
│       ├── base_dictionary.py    # 🧑‍🏭 工种字典 (WorkType)
│       ├── data_category_dictionary.py  # 📂 数据类别字典 (DataCategory)
│       ├── data_pool_dictionary.py   # 🗃️ 数据池字典 (DataPool)
│       ├── dataset_dictionary.py     # 📊 数据集字典 (DatasetItem)
│       └── data_attribute_dictionary.py  # 📋 属性模板字典 (AttributeTemplate)
│
└── templates/                     # 📋 Excel 数据导入模板
    ├── Data_Import_Template.xlsx       # 🔷 全量数据导入模板（5字典完整版）
    ├── Data_Import_Template_Simple.xlsx # ⚡ 快速数据导入模板（仅4列）
    ├── text_data_template.xlsx        # 📝 文本数据存储模板
    └── image_data_template.xlsx       # 🖼️ 图像数据存储模板
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
