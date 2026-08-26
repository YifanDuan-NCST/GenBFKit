# GenBFKit Performance Evaluation Task Set
# GenBFKit 性能评估任务集

## 1. Purpose
## 1. 研究目的
This document defines the standardized task set used for the performance evaluation of GenBFKit and the reference systems.
本文档定义了用于GenBFKit及对照系统性能评估的标准化任务集。

The task set is designed to provide a consistent basis for measuring **data-integration efficiency, single-task data access time, parameter standardization rate, cross-task data reusability, model deployment adaptation, and user experience**.
该任务集旨在为测评**数据整合效率、单任务数据访问耗时、参数标准化率、跨任务数据复用性、模型部署适配性及用户使用体验**提供统一基准。

All evaluated systems should use the same input data, task requirements, output requirements, and evaluation criteria.
所有参评系统均需采用统一的输入数据、任务要求、输出规范与评估标准。

The tasks are derived from representative intelligent blast furnace (BF) scenarios described in the manuscript, covering **BF operational status evaluation, abnormal diagnosis, hot-metal silicon-content prediction, process optimization, and burden-scheme calculation**.
所有任务均源自论文中典型的高炉智能化应用场景，涵盖**高炉运行状态评估、异常工况诊断、铁水硅含量预测、工艺优化及配料方案计算**五大场景。

---

# Task 1. BF Operational Status Evaluation
# 任务一：高炉运行状态评估
### Task ID
### 任务编号
`T1_BF_Status_Evaluation`

### Task category
### 任务类型
**Status evaluation**
**状态评估**

### Background
### 任务背景
Evaluate the operational status of the blast furnace using process monitoring parameters and relevant auxiliary information.
依托工艺监测参数及相关辅助信息，对高炉的整体运行状态进行评估。

### Data requirements
### 数据要求
The task should use representative BF process parameters, including:
本任务需采用高炉典型工艺参数，具体包括：
- Furnace-top pressure; 炉顶压力
- Furnace-hearth temperature-related parameters; 炉缸温度相关参数
- Blast-related parameters; 鼓风相关参数
- Gas-related parameters; 煤气相关参数
- Other key BF operating parameters available through the standardized data dictionary. 标准化数据字典中可获取的其他高炉关键运行参数

The task may additionally use equipment maintenance or operation records as auxiliary information.
本任务可额外依托设备运维记录、生产操作记录作为辅助数据。

### Task requirements
### 任务要求
Participants are required to:
参评系统需完成以下操作：
1. Identify the relevant data sources and parameters for BF operational status evaluation; 甄别高炉运行状态评估所需的数据源及核心参数；
2. Import or access the required data; 导入或调取所需业务数据；
3. Standardize the parameter names and formats; 完成参数名称与数据格式的标准化处理；
4. Retrieve the task-relevant parameter subset; 筛选并提取本任务所需的参数子集；
5. Generate the formatted dataset required for downstream status evaluation. 生成可供下游状态评估使用的标准化数据集。

### Required output
### 输出要求
The final output should include:
最终输出成果需包含：
- Task-relevant parameter list; 任务相关参数清单；
- Parameter names and corresponding metadata; 参数名称及对应元数据信息；
- Data source and storage information; 数据源及数据存储信息；
- Standardized dataset; 标准化数据集；
- Data access result suitable for downstream BF status evaluation. 可直接用于下游高炉状态评估的数据调用结果。

### Evaluation metrics
### 评估指标
This task is primarily used to evaluate:
本任务主要用于测评：
- Data integration time; 数据整合耗时；
- Single-task data access time; 单任务数据访问耗时；
- Parameter standardization rate; 参数标准化率；
- Task completion rate; 任务完成率；
- User learning time. 用户上手学习耗时。

---

# Task 2. BF Abnormal Condition Diagnosis
# 任务二：高炉异常工况诊断
### Task ID
### 任务编号
`T2_BF_Anomaly_Diagnosis`

### Task category
### 任务类型
**Abnormal diagnosis**
**异常诊断**

### Background
### 任务背景
Construct a task-oriented dataset for detecting and diagnosing abnormal BF operating conditions.
构建面向任务的数据集，实现高炉异常工况的检测与诊断分析。

### Data requirements
### 数据要求
The task should include representative parameters related to abnormal BF conditions, such as:
本任务需包含高炉异常工况相关的典型参数，具体如下：
- Furnace-hearth temperature; 炉缸温度；
- Furnace-top pressure; 炉顶压力；
- Blast-related parameters; 鼓风相关参数；
- Cooling-related parameters; 冷却相关参数；
- Other process parameters associated with BF condition changes. 其他与高炉工况波动相关的工艺参数。

Where available, burden surface images or equipment maintenance records may be used as auxiliary information.
在数据可获取的前提下，可将料面图像、设备运维记录作为辅助数据使用。

### Task requirements
### 任务要求
Participants are required to:
参评系统需完成以下操作：
1. Identify the process variables relevant to abnormal-condition diagnosis; 甄别异常工况诊断所需的工艺变量；
2. Retrieve the corresponding data from the standardized data architecture; 从标准化数据架构中调取对应数据；
3. Check parameter naming, format and metadata consistency; 校验参数名称、数据格式及元数据的一致性；
4. Construct a structured dataset for abnormal-condition analysis; 构建适用于异常工况分析的结构化数据集；
5. Provide the final parameter subset and formatted output. 输出最终参数子集及标准化成果数据。

### Required output
### 输出要求
The final output should include:
最终输出成果需包含：
- Retrieved abnormal-diagnosis parameters; 调取的异常诊断核心参数；
- Corresponding parameter metadata; 对应参数的元数据信息；
- Standardized data tables; 标准化数据表；
- Data required for downstream anomaly diagnosis. 下游异常诊断任务所需的完整数据。

### Evaluation metrics
### 评估指标
This task is primarily used to evaluate:
本任务主要用于测评：
- Single-task data access time; 单任务数据访问耗时；
- Parameter standardization rate; 参数标准化率；
- Data integrity retention rate; 数据完整性留存率；
- Task completion rate; 任务完成率；
- Cross-task data reuse rate. 跨任务数据复用率。

---

# Task 3. Hot-metal Silicon-content Prediction
# 任务三：铁水硅含量预测
### Task ID
### 任务编号
`T3_HotMetal_Silicon_Prediction`

### Task category
### 任务类型
**Parameter prediction**
**参数预测**

### Background
### 任务背景
Construct a standardized dataset for predicting the silicon content of hot metal.
构建用于铁水硅含量预测的标准化数据集。

This task corresponds directly to the functional verification task used in the manuscript.
本任务为论文中核心的功能验证测试任务。

### Data requirements
### 数据要求
The task uses the parameter categories identified by the task-oriented retrieval module:
本任务采用面向任务检索模块划分的四大参数类别：
- **BFHM**: Basic features of hot metal; **BFHM**：铁水基础特征；
- **FRM**: Features of raw materials; **FRM**：原料特征；
- **BDP**: Burden distribution parameters; **BDP**：布料参数；
- **PP**: Process parameters. **PP**：工艺参数。

Representative parameters include:
具体典型参数如下：

- Si content of hot metal (`Si_C`); 铁水硅含量（`Si_C`）
- C content (`C_C`); 碳含量（`C_C`）
- Fe content (`Fe_C`); 铁含量（`Fe_C`）
- Mn content (`Mn_C`); 锰含量（`Mn_C`）
- Ti content (`Ti_C`); 钛含量（`Ti_C`）
- SiO₂ content of sinter (`SiO2_S`); 烧结矿二氧化硅含量（`SiO2_S`）
- SiO₂ content of pellet (`SiO2_P`); 球团矿二氧化硅含量（`SiO2_P`）
- Average particle size of coke (`APS_C`); 焦炭平均粒径（`APS_C`）
- Total weight of sinter feed bin (`TW_S`); 烧结矿料仓总重（`TW_S`）
- Total weight of pellet feed bin (`TW_P`); 球团矿料仓总重（`TW_P`）
- Batch weight of coke (`BW_C`); 焦炭批次重量（`BW_C`）
- Batch weight of ore (`BW_O`); 矿石批次重量（`BW_O`）
- Furnace-top pressure (`PFT`); 炉顶压力（`PFT`）
- Average furnace-hearth shell temperature (`ATFHS`); 炉缸外壳平均温度（`ATFHS`）
- Average furnace-lining temperature (`ATFL`); 炉衬平均温度（`ATFL`）
- Oxygen-enriched flow rate (`FROE`); 富氧流量（`FROE`）
- Permeability index (`PI`); 透气性指数（`PI`）
- Blast kinetic energy (`BKE`); 鼓风动能（`BKE`）
- Furnace-hearth activity (`FHA`); 炉缸活性（`FHA`）
- Gas utilization rate (`GUR`). 煤气利用率（`GUR`）

### Task requirements
### 任务要求
Participants are required to:
参评系统需完成以下操作：
1. Input the task requirement for hot-metal silicon-content prediction; 录入铁水硅含量预测的任务需求；
2. Retrieve task-relevant parameters using the available data-access mechanism; 通过数据访问机制调取任务相关参数；
3. Obtain parameters from different data pools; 从多类数据池中采集所需参数；
4. Standardize parameter names and formats; 完成参数名称与格式的标准化处理；
5. Assemble the final structured prediction dataset. 整合生成最终的结构化预测数据集。

### Required output
### 输出要求
The final output should include:
最终输出成果需包含：
- Task-specific parameter subset; 任务专属参数子集；
- Parameter category; 参数所属类别；
- Data pool; 对应数据池；
- Parameter name and unit; 参数名称及单位；
- Standardized dataset for silicon-content prediction. 用于硅含量预测的标准化数据集。

### Evaluation metrics
### 评估指标
This task is the **primary benchmark task** for:
本任务为核心基准测试任务，用于测评：
- Task-oriented retrieval; 面向任务的数据检索能力；
- Single-task data access time; 单任务数据访问耗时；
- Parameter standardization rate; 参数标准化率；
- Cross-task data reuse rate; 跨任务数据复用率；
- Model deployment adaptation rate; 模型部署适配率；
- Task completion rate. 任务完成率。

The manuscript reports that the task-oriented retrieval module retrieves parameters through the hierarchical structure: `Work type → Data category → Data pool → Dataset → Data attribute` and subsequently ranks candidate parameters using the retrieval and matching mechanism.
论文表明，面向任务的检索模块通过**作业类型→数据类别→数据池→数据集→数据属性**的层级结构检索参数，并依托检索匹配机制完成候选参数排序。

---

# Task 4. BF Process Optimization
# 任务四：高炉工艺优化
### Task ID
### 任务编号
`T4_BF_Process_Optimization`

### Task category
### 任务类型
**Process optimization**
**工艺优化**

### Background
### 任务背景
Construct the data required for BF process optimization and regulation.
构建高炉工艺优化与调控所需的标准化数据。

### Data requirements
### 数据要求
The task should include controllable and response-related process parameters, such as:
本任务需包含工艺可控变量与工况响应类参数，具体如下：
- Blast kinetic energy; 鼓风动能；
- Blast-related operating parameters; 鼓风操作相关参数；
- Furnace-hearth activity; 炉缸活性；
- Relevant process response parameters; 相关工艺响应参数；
- Other controllable and response variables required for the optimization task. 优化任务所需的其他可控变量与响应变量。

### Task requirements
### 任务要求
Participants are required to:
参评系统需完成以下操作：
1. Identify controllable variables and corresponding response variables; 甄别优化任务所需的可控变量与对应工况响应变量；
2. Retrieve the required parameter groups from the standardized data architecture; 从标准化数据架构中调取所需参数组；
3. Verify the correspondence between control variables and process responses; 校验可控变量与工艺响应之间的对应关系；
4. Generate the structured dataset required for optimization analysis. 生成可供工艺优化分析使用的结构化数据集。

### Required output
### 输出要求
The final output should include:
最终输出成果需包含：
- Controllable parameters; 可控工艺参数；
- Response parameters; 工况响应参数；
- Corresponding metadata; 对应元数据信息；
- Parameter-to-task mapping; 参数与任务匹配关系；
- Standardized process-optimization dataset. 标准化工艺优化数据集。

### Evaluation metrics
### 评估指标
This task is primarily used to evaluate:
本任务主要用于测评：
- Data integration time; 数据整合耗时；
- Single-task data access time; 单任务数据访问耗时；
- Data integrity retention rate; 数据完整性留存率；
- Cross-task data reuse rate; 跨任务数据复用率；
- Task completion rate. 任务完成率。

---

# Task 5. Burden-scheme Calculation and Cost Reduction
# 任务五：配料方案计算与成本优化
### Task ID
### 任务编号
`T5_Burden_Cost_Reduction`

### Task category
### 任务类型
**Cost reduction**
**成本优化**

### Background
### 任务背景
Construct the data required for burden-scheme calculation and raw-material optimization.
构建用于高炉配料方案计算与原料优化的标准化数据集。

### Data requirements
### 数据要求
The task should use batch-type data and constraint data related to burden feeding, including:
本任务需采用高炉上料相关的批次数据与约束条件数据，具体包括：
- Raw-material composition; 原料成分数据；
- Sinter composition; 烧结矿成分数据；
- Pellet composition; 球团矿成分数据；
- Coke-related parameters; 焦炭相关参数；
- Sinter feed-bin weight; 烧结矿料仓重量参数；
- Pellet feed-bin weight; 球团矿料仓重量参数；
- Coke batch weight; 焦炭批次上料重量；
- Ore batch weight; 矿石批次上料重量；
- Material-balance constraints; 物料平衡约束条件；
- Other available burden-feeding parameters. 其他可获取的高炉上料相关参数。

### Task requirements
### 任务要求
Participants are required to:
参评系统需完成以下操作：
1. Identify the raw-material and burden-feeding data required by the task; 甄别任务所需的原料数据与高炉上料参数；
2. Retrieve the corresponding batch-type and constraint data; 调取对应的批次数据与约束条件数据；
3. Standardize parameter names, formats and units; 完成参数名称、格式、计量单位的标准化处理；
4. Construct a structured dataset for burden-scheme calculation; 构建适用于配料方案计算的结构化数据集；
5. Provide the associated constraints required for downstream optimization. 提供下游优化任务所需的配套约束条件。

### Required output
### 输出要求
The final output should include:
最终输出成果需包含：
- Raw-material composition parameters; 原料成分参数；
- Burden-feeding parameters; 高炉上料配料参数；
- Constraint parameters; 优化约束条件参数；
- Corresponding metadata; 对应元数据信息；
- Standardized dataset for burden-scheme calculation. 用于配料方案计算的标准化数据集。

### Evaluation metrics
### 评估指标
This task is primarily used to evaluate:
本任务主要用于测评：
- Single-task data access time; 单任务数据访问耗时；
- Parameter standardization rate; 参数标准化率；
- Data integrity retention rate; 数据完整性留存率；
- Cross-task data reuse rate; 跨任务数据复用率；
- Task completion rate. 任务完成率。

---

# Cross-task Reuse Evaluation
# 跨任务复用性评估
The above five tasks are jointly used to evaluate the ability of GenBFKit to reuse standardized data across different downstream intelligent tasks.
以上五项任务联合用于测评 GenBFKit 在多类下游智能任务中的标准化数据复用能力。

A parameter is considered **cross-task reusable** when it can be directly invoked by at least two of the five predefined tasks without:
满足以下全部条件时，该参数判定为**可跨任务复用参数**，可被至少两项预设任务直接调用，且无需：

1. Re-acquiring the raw data; 重新采集原始数据；
2. Re-defining the parameter mapping; 重新定义参数映射关系；
3. Reconstructing the underlying storage schema. 重构底层数据存储结构。

The cross-task data reuse rate is calculated as:
跨任务数据复用率计算公式如下：

$$
R_{\mathrm{reuse}}
=
\frac{N_{\mathrm{reusable}}}
{N_{\mathrm{integrated}}}
\times 100\%
$$

where:
公式参数说明：
- $R_{\mathrm{reuse}}$: cross-task data reuse rate; $R_{\mathrm{reuse}}$：跨任务数据复用率；
- $N_{\mathrm{reusable}}$: number of standardized parameters directly reusable by at least two tasks; $N_{\mathrm{reusable}}$：可被至少两项任务直接复用的标准化参数数量；
- $N_{\mathrm{integrated}}$: total number of standardized parameters included in the evaluation. $N_{\mathrm{integrated}}$：本次测评纳入统计的全部标准化参数总数。

---

# Task Execution Protocol
# 任务执行规范
For each benchmark task, all evaluated systems should follow the same experimental protocol.
所有参评系统在每项基准任务测试中，均需遵循统一实验执行规范。

### Step 1. Task instruction
### 步骤一：任务下发
Participants receive the same task description, data scope and expected output requirements.
参评系统接收统一的任务说明、数据范围与输出规范要求。

### Step 2. System initialization
### 步骤二：系统初始化
The required data sources and task configuration are initialized according to the standardized experimental environment.
基于标准化实验环境，完成数据源与任务配置的初始化操作。

### Step 3. Data integration
### 步骤三：数据整合
Participants complete the required data import, parameter mapping, metadata registration and standardized storage operations.
完成数据导入、参数映射、元数据登记及标准化存储等全部整合操作。

### Step 4. Task-oriented data access
### 步骤四：面向任务数据调取
Participants retrieve the task-specific parameter subset and generate the required formatted output.
检索获取任务专属参数子集，生成符合规范的格式化输出结果。

### Step 5. Result validation
### 步骤五：结果校验
The output is checked against the predefined task requirements, including:
对照预设任务规范对输出结果进行校验，校验维度包括：
- Parameter completeness; 参数完整性；
- Naming consistency; 命名一致性；
- Format consistency; 格式一致性；
- Metadata integrity; 元数据完整性；
- Task relevance; 任务相关性；
- Output completeness. 输出完整性。

# Recommended Use in the GenBFKit Benchmark
# GenBFKit基准测试使用说明
The five tasks should be treated as a **standardized task suite rather than five independent demonstrations**.
五项任务需作为**标准化任务套件整体使用**，而非五项独立测试案例。

The purpose is to evaluate whether the same standardized BF data resources can support multiple downstream intelligent tasks through task-oriented retrieval, thereby testing the central design principle of GenBFKit:
核心测评目的为验证统一的高炉标准化数据资源，可通过面向任务检索支撑多项下游智能任务，以此检验GenBFKit的核心设计理念：

**One-time data integration → standardized governance → multi-task data reuse**
**一次数据整合 → 标准化治理 → 多任务数据复用**
