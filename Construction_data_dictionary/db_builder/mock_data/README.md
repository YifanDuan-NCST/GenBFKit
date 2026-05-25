# GenBFKit Mock Data Generator

为 GenBFKit 框架中所有物理数据表自动生成真实感的高炉炼铁行业虚拟数据。

## 功能特性

- **智能类型推断**: 根据列名和 PostgreSQL 列类型自动选择最合适的数据生成策略
- **高炉炼铁行业词汇**: 内置炼铁专业术语库（温度、压力、流量、成分等）
- **9种数据池全覆盖**: 支持所有数据池类型（连续时序、离散时序、二元状态、批次、约束、可控、响应、文本、图像）
- **批量插入**: 支持大批量数据生成，每批 500 行
- **幂等模式**: `upsert` 模式——已满 100 行则跳过，不重复插入
- **详细报告**: 每次运行生成完整统计报告，包含耗时、成功率、失败详情

## 快速开始

### 方式一：命令行运行

```bash
cd Construction_data_dictionary

# 生成所有表，每表 100 行
python db_builder/mock_data/main.py

# 每表 50 行，使用固定种子（可复现）
python db_builder/mock_data/main.py --rows 50 --seed 42

# 先清空再插入（覆盖模式）
python db_builder/mock_data/main.py --mode overwrite

# 仅测试前 10 张表
python db_builder/mock_data/main.py --max 10

# 静默模式
python db_builder/mock_data/main.py --quiet
```

### 方式二：API 调用

```bash
# 生成所有表数据
curl -X POST "http://localhost:8000/api/mock/generate-all?rows=100"

# 生成单个表数据
curl -X POST "http://localhost:8000/api/mock/generate?table_name=xxx"

# 查看生成状态
curl "http://localhost:8000/api/mock/status"

# 预览表数据
curl "http://localhost:8000/api/mock/preview/xxx?limit=5"
```

### 方式三：Python 脚本调用

```python
from db_builder.mock_data import MockDataGenerator

# 初始化（每表 100 行）
generator = MockDataGenerator(rows_per_table=100, seed=42)

# 生成所有表
stats = generator.generate_all(mode="upsert")

# 生成单个表
result = generator.generate_for_table("table_name")

# 预览表数据
preview = generator.preview_table_data("table_name", limit=5)
```

## 命令行参数

| 参数 | 缩写 | 默认值 | 说明 |
|------|------|--------|------|
| `--rows` | `-r` | 100 | 每个表生成的行数 |
| `--seed` | `-s` | None | 随机数种子，固定则每次生成相同数据 |
| `--mode` | `-m` | upsert | `upsert`=已满跳过，`overwrite`=先清空再插入 |
| `--max` | `-n` | None | 最多处理的表数（用于测试） |
| `--batch` | `-b` | 500 | 每批插入的行数 |
| `--quiet` | `-q` | False | 静默模式，不打印详细日志 |

## 数据生成策略

### 列名智能推断

| 列名关键词 | 生成策略 | 示例 |
|-----------|---------|------|
| `temp` / `temperature` | 高炉区域温度 | 炉缸 1400-1550°C, 风口 2000-2400°C |
| `pressure` / `press` | 高炉区域压力 | 热风压力 200-600 kPa |
| `flow` / `flux` | 流量数据 | 风量 150000-300000 Nm³/h |
| `composition` / `成分` | 成分分析 | Fe 55-70%, Si 0.1-1.5% |
| `value` / `mean` / `avg` | 数值数据 | 0-1000 范围浮点数 |
| `status` / `flag` / `enabled` | 布尔状态 | True / False |
| `timestamp` / `time` | 时间戳 | 2024-2025 年随机时间 |
| `count` / `number` | 计数器 | 整数序列 |
| `type` / `grade` | 枚举值 | A / B / C / D |
| `batch` / `lot` | 批次号 | BATCH_20240115_0001 |
| `heat` / `炉次` | 炉次号 | HEAT_20240115_001 |
| `tag` / `标签` | JSONB 标签列表 | ["critical", "monitored"] |
| `keyword` | JSONB 关键词列表 | ["blast_furnace", "ironmaking"] |
| `rule` / `规则` | JSONB 规则集 | {"min": 0, "max": 100} |

### 高炉炼铁专业数据范围

| 参数类型 | 范围 | 单位 |
|---------|------|------|
| 炉缸温度 | 1400-1550 | °C |
| 风口区温度 | 2000-2400 | °C |
| 炉腹温度 | 1200-1450 | °C |
| 炉顶温度 | 100-400 | °C |
| 热风压力 | 200-600 | kPa |
| 炉顶煤气压力 | 50-250 | kPa |
| 风量 | 150000-300000 | Nm³/h |
| 炉顶煤气量 | 100000-200000 | Nm³/h |
| 铁水成分 Fe | 55-70 | % |
| 铁水成分 Si | 0.1-1.5 | % |
| 炉渣成分 CaO | 20-45 | % |

## 文件结构

```
db_builder/mock_data/
├── __init__.py       # 包入口
├── generator.py      # 核心生成引擎
├── main.py           # CLI 入口脚本
└── README.md         # 本文档
```

## 注意事项

1. **幂等性**: 默认 `upsert` 模式，已满 100 行的表不会被重复写入
2. **随机种子**: 使用 `--seed` 参数可以固定随机数，生成可复现的测试数据
3. **性能**: 批量插入（每批 500 行），对 2128 张表约需数分钟
4. **依赖**: 需要 PostgreSQL 数据库已启动，且 `prebuilt_full.json` 已导入
5. **dataset_id**: 插入数据时会自动从 `meta_datasets` 表获取对应 UUID
