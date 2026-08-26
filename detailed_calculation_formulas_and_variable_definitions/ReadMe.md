# Appendix L. Quantitative Definitions and Calculation Methods for Evaluation Metrics
# 附录 L. 评价指标的定量定义与计算方法

To improve the reproducibility and quantitative transparency of the performance evaluation, this Appendix provides explicit calculation formulas and variable definitions for all indicators listed in Table 9. Unless otherwise specified, repeated measurements are first aggregated at the participant or experimental-unit level, followed by calculation of the overall mean and standard deviation.

为提高性能评价的可重复性与定量透明度，本附录对 Table 9 中列出的全部评价指标给出明确的计算公式及变量定义。除非另有说明，对于重复测量数据，首先在参与者或实验单元层面进行汇总，然后进一步计算总体均值和标准差。

---

## L.1. Data-processing efficiency
## L.1. 数据处理效率

### L.1.1 Data integration time
### L.1.1 数据整合时间

**Definition in Table 9:**  
**Table 9 中的定义：**

Total time required to transform fragmented raw data into a standardized dataset.

从碎片化原始数据处理至标准化数据集生成所需的总处理时间。

The data integration time is defined as:

数据整合时间定义为：

$$
T_{\mathrm{int}} = t_{\mathrm{end}} - t_{\mathrm{start}}
$$

where:

其中：

- $T_{\mathrm{int}}$: data integration time, in hours (h);  
  $T_{\mathrm{int}}$：数据整合时间，单位为小时（h）；
- $t_{\mathrm{start}}$: start time of the data integration procedure;  
  $t_{\mathrm{start}}$：数据整合过程的开始时间；
- $t_{\mathrm{end}}$: end time at which the standardized dataset has been generated and validated.  
  $t_{\mathrm{end}}$：标准化数据集生成并完成验证的结束时间。

The integration procedure includes data import, parameter mapping, metadata registration, format validation, and standardized storage.

数据整合过程包括数据导入、参数映射、元数据注册、格式校验以及标准化存储。

For $N$ valid experimental observations, the mean data integration time is:

对于 $N$ 个有效实验观测值，平均数据整合时间计算为：

$$
\overline{T}_{\mathrm{int}}
=
\frac{1}{N}
\sum_{i=1}^{N}
T_{\mathrm{int},i}
$$

where:

其中：

- $\overline{T}_{\mathrm{int}}$: mean data integration time;  
  $\overline{T}_{\mathrm{int}}$：平均数据整合时间；
- $T_{\mathrm{int},i}$: integration time of the $i$-th observation;  
  $T_{\mathrm{int},i}$：第 $i$ 次观测对应的数据整合时间；
- $N$: number of valid observations.  
  $N$：有效观测值数量。

For comparison with a baseline system, the relative reduction in integration time is:

与 baseline 系统进行比较时，数据整合时间的相对降低率定义为：

$$
\eta_{\mathrm{int}}
=
\frac{
T_{\mathrm{baseline}}-T_{\mathrm{GenBFKit}}
}{
T_{\mathrm{baseline}}
}
\times 100\%
$$

where:

其中：

- $\eta_{\mathrm{int}}$: relative reduction in data integration time;  
  $\eta_{\mathrm{int}}$：数据整合时间的相对降低率；
- $T_{\mathrm{baseline}}$: mean integration time of the reference system;  
  $T_{\mathrm{baseline}}$：参考系统的平均数据整合时间；
- $T_{\mathrm{GenBFKit}}$: mean integration time of GenBFKit.  
  $T_{\mathrm{GenBFKit}}$：GenBFKit 的平均数据整合时间。

---

### L.1.2 Single-task data access time
### L.1.2 单任务数据访问时间

**Definition in Table 9:**  
**Table 9 中的定义：**

Time required to retrieve and format data for a specified downstream intelligent task.

针对下游智能化任务完成数据检索并生成规定格式输出所需的时间。

The single-task data access time is calculated as:

单任务数据访问时间计算为：

$$
T_{\mathrm{access}}
=
t_{\mathrm{output}}-t_{\mathrm{query}}
$$

where:

其中：

- $T_{\mathrm{access}}$: single-task data access time, in minutes (min);  
  $T_{\mathrm{access}}$：单任务数据访问时间，单位为分钟（min）；
- $t_{\mathrm{query}}$: time at which the task-oriented query is submitted;  
  $t_{\mathrm{query}}$：任务导向查询提交的时间；
- $t_{\mathrm{output}}$: time at which the required data are completely retrieved and formatted.  
  $t_{\mathrm{output}}$：所需数据完成检索并生成规定格式输出的时间。

For $N$ valid retrieval trials:

对于 $N$ 次有效检索实验：

$$
\overline{T}_{\mathrm{access}}
=
\frac{1}{N}
\sum_{i=1}^{N}
T_{\mathrm{access},i}
$$

The relative reduction compared with a baseline is:

相对于 baseline 的相对降低率为：

$$
\eta_{\mathrm{access}}
=
\frac{
T_{\mathrm{access,baseline}}
-
T_{\mathrm{access,GenBFKit}}
}{
T_{\mathrm{access,baseline}}
}
\times 100\%
$$

where:

其中：

- $\eta_{\mathrm{access}}$: relative reduction in single-task data access time;  
  $\eta_{\mathrm{access}}$：单任务数据访问时间的相对降低率；
- $T_{\mathrm{access,baseline}}$: mean access time of the reference system;  
  $T_{\mathrm{access,baseline}}$：参考系统的平均访问时间；
- $T_{\mathrm{access,GenBFKit}}$: mean access time of GenBFKit.  
  $T_{\mathrm{access,GenBFKit}}$：GenBFKit 的平均访问时间。

---

### L.1.3 Parameter standardization rate
### L.1.3 参数标准化率

**Definition in Table 9:**  
**Table 9 中的定义：**

Proportion of parameters with unified naming, formatting and metadata specifications.

满足统一命名和格式规范的参数占全部评价参数的比例。

The parameter standardization rate is:

参数标准化率定义为：

$$
R_{\mathrm{std}}
=
\frac{N_{\mathrm{std}}}
{N_{\mathrm{total}}}
\times 100\%
$$

where:

其中：

- $R_{\mathrm{std}}$: parameter standardization rate;  
  $R_{\mathrm{std}}$：参数标准化率；
- $N_{\mathrm{std}}$: number of parameters satisfying the predefined standardization requirements;  
  $N_{\mathrm{std}}$：满足预定义标准化要求的参数数量；
- $N_{\mathrm{total}}$: total number of evaluated parameters.  
  $N_{\mathrm{total}}$：参与评价的参数总数。

A parameter is considered standardized only when its required naming, format, and metadata specifications are simultaneously satisfied.

仅当参数同时满足预定义的命名、格式和元数据规范时，才将其判定为已标准化参数。

For multiple datasets:

对于多个数据集：

$$
R_{\mathrm{std,overall}}
=
\frac{
\sum_{k=1}^{K}N_{\mathrm{std},k}
}{
\sum_{k=1}^{K}N_{\mathrm{total},k}
}
\times 100\%
$$

where:

其中：

- $K$: number of evaluated datasets or experimental groups;  
  $K$：评价数据集或实验组的数量；
- $N_{\mathrm{std},k}$: standardized parameter count in dataset $k$;  
  $N_{\mathrm{std},k}$：第 $k$ 个数据集中的标准化参数数量；
- $N_{\mathrm{total},k}$: total parameter count in dataset $k$.  
  $N_{\mathrm{total},k}$：第 $k$ 个数据集中的参数总数。

---

## L.2. Storage performance
## L.2. 存储性能

### L.2.1 Storage compression ratio
### L.2.1 存储压缩比

**Definition in Table 9:**  
**Table 9 中的定义：**

Volume ratio of standardized storage to original data storage.

标准化存储数据体积与原始数据存储体积之比。

The storage compression ratio is:

存储压缩比定义为：

$$
C_{\mathrm{storage}}
=
\frac{V_{\mathrm{std}}}
{V_{\mathrm{raw}}}
$$

where:

其中：

- $C_{\mathrm{storage}}$: storage compression ratio;  
  $C_{\mathrm{storage}}$：存储压缩比；
- $V_{\mathrm{std}}$: storage volume of the standardized dataset;  
  $V_{\mathrm{std}}$：标准化数据集占用的存储空间；
- $V_{\mathrm{raw}}$: storage volume of the corresponding original dataset.  
  $V_{\mathrm{raw}}$：对应原始数据集占用的存储空间。

A smaller value indicates lower storage occupation relative to the original data.

该指标数值越小，表示相对于原始数据所占用的存储空间越少。

For multiple datasets:

对于多个数据集：

$$
C_{\mathrm{storage,overall}}
=
\frac{
\sum_{k=1}^{K}V_{\mathrm{std},k}
}{
\sum_{k=1}^{K}V_{\mathrm{raw},k}
}
$$

---

### L.2.2 Query response time
### L.2.2 查询响应时间

**Definition in Table 9:**  
**Table 9 中的定义：**

Average response latency of conditional data query.

条件数据查询的平均响应延迟。

For each query:

对于每次查询：

$$
T_{\mathrm{query}}
=
t_{\mathrm{return}}
-
t_{\mathrm{submit}}
$$

where:

其中：

- $T_{\mathrm{query}}$: query response time, in minutes (min);  
  $T_{\mathrm{query}}$：查询响应时间，单位为分钟（min）；
- $t_{\mathrm{submit}}$: query submission time;  
  $t_{\mathrm{submit}}$：查询提交时间；
- $t_{\mathrm{return}}$: time at which the complete query result is returned.  
  $t_{\mathrm{return}}$：完整查询结果返回的时间。

For $N$ valid queries:

对于 $N$ 次有效查询：

$$
\overline{T}_{\mathrm{query}}
=
\frac{1}{N}
\sum_{i=1}^{N}
T_{\mathrm{query},i}
$$

The relative response-time reduction is:

查询响应时间的相对降低率为：

$$
\eta_{\mathrm{query}}
=
\frac{
T_{\mathrm{query,baseline}}
-
T_{\mathrm{query,GenBFKit}}
}{
T_{\mathrm{query,baseline}}
}
\times 100\%
$$

---

### B.3 Data integrity retention rate
### B.3 数据完整性保持率

**Definition in Table 9:**  
**Table 9 中的定义：**

Retention degree of original information, measured by coverage of key fields.

通过关键字段覆盖率衡量原始信息的保留程度。

The data integrity retention rate is:

数据完整性保持率定义为：

$$
R_{\mathrm{integrity}}
=
\frac{N_{\mathrm{retained}}}
{N_{\mathrm{key}}}
\times 100\%
$$

where:

其中：

- $R_{\mathrm{integrity}}$: data integrity retention rate;  
  $R_{\mathrm{integrity}}$：数据完整性保持率；
- $N_{\mathrm{retained}}$: number of key fields correctly retained after data processing;  
  $N_{\mathrm{retained}}$：数据处理后正确保留的关键字段数量；
- $N_{\mathrm{key}}$: total number of predefined key fields.  
  $N_{\mathrm{key}}$：预定义关键字段总数。

For multiple datasets:

对于多个数据集：

$$
R_{\mathrm{integrity,overall}}
=
\frac{
\sum_{k=1}^{K}N_{\mathrm{retained},k}
}{
\sum_{k=1}^{K}N_{\mathrm{key},k}
}
\times 100\%
$$

---

## L.3. Cross-task generalization ability
## L.3. 跨任务泛化能力

### L.3.1 Cross-task data reuse rate
### L.3.1 跨任务数据复用率

**Definition in Table 9:**  
**Table 9 中的定义：**

Proportion of standardized parameters that can be directly reused by at least two downstream tasks.

可以被至少两个下游任务直接复用的标准化参数的比例。

To make *directly applicable* operationally measurable, a parameter is regarded as reusable when it can be directly invoked by at least two predefined downstream intelligent tasks without repeated raw-data acquisition, parameter remapping, or reconstruction of the underlying storage schema.

为了使“直接可应用”具有可操作的定量定义，当某一参数能够被至少两个预定义下游智能任务直接调用，且无需重新进行原始数据采集、参数映射或底层存储结构重构时，将该参数定义为可复用参数。

The cross-task data reuse rate is:

跨任务数据复用率定义为：

$$
R_{\mathrm{reuse}}
=
\frac{N_{\mathrm{reusable}}}
{N_{\mathrm{integrated}}}
\times 100\%
$$

where:

其中：

- $R_{\mathrm{reuse}}$: cross-task data reuse rate;  
  $R_{\mathrm{reuse}}$：跨任务数据复用率；
- $N_{\mathrm{reusable}}$: number of standardized parameters that can be directly reused by at least two downstream tasks;  
  $N_{\mathrm{reusable}}$：能够被至少两个下游任务直接复用的标准化参数数量；
- $N_{\mathrm{integrated}}$: total number of standardized parameters included in the evaluation.  
  $N_{\mathrm{integrated}}$：参与评价的标准化参数总数。

For parameter $p$, define the reuse indicator:

对于参数 $p$，定义复用指示变量：

$$
I_p
=
\begin{cases}
1, & n_{\mathrm{task}}(p)\geq 2 \\
0, & n_{\mathrm{task}}(p)<2
\end{cases}
$$

where:

其中：

- $I_p$: reuse indicator of parameter $p$;  
  $I_p$：参数 $p$ 的复用指示变量；
- $n_{\mathrm{task}}(p)$: number of predefined downstream tasks that can directly invoke parameter $p$.  
  $n_{\mathrm{task}}(p)$：能够直接调用参数 $p$ 的预定义下游任务数量。

Then:

则：

$$
N_{\mathrm{reusable}}
=
\sum_{p=1}^{N_{\mathrm{integrated}}}
I_p
$$

and therefore:

因此：

$$
R_{\mathrm{reuse}}
=
\frac{
\sum_{p=1}^{N_{\mathrm{integrated}}}I_p
}{
N_{\mathrm{integrated}}
}
\times 100\%
$$

This definition distinguishes genuine cross-task reuse from repeated access to the same database by only one task.

该定义能够区分真正的跨任务数据复用与单一任务对同一数据库的重复访问。

---

### L.3.2 Model deployment adaptation rate
### L.3.2 模型部署适配率

**Definition in Table 9:**  
**Table 9 中的定义：**

Proportion of downstream models whose performance reaches the corresponding baseline performance under the same task, input data and evaluation metric.

在相同的任务、输入数据和评价指标下，性能达到相应基线性能的下游模型比例。

For downstream model $m$, let:

对于下游模型 $m$：

- $S_{\mathrm{base},m}$: baseline performance of model $m$;  
  $S_{\mathrm{base},m}$：模型 $m$ 的 baseline performance；
- $S_{\mathrm{int},m}$: performance of model $m$ when driven by GenBFKit-integrated data.  
  $S_{\mathrm{int},m}$：使用 GenBFKit 集成数据驱动模型 $m$ 时获得的性能。

When a higher value represents better model performance:

当模型性能指标数值越大代表性能越好时：

$$
A_m
=
\begin{cases}
1, & S_{\mathrm{int},m}\geq S_{\mathrm{base},m} \\
0, & S_{\mathrm{int},m}<S_{\mathrm{base},m}
\end{cases}
$$

The model deployment adaptation rate is:

模型部署适配率定义为：

$$
R_{\mathrm{adapt}}
=
\frac{N_{\mathrm{adapted}}}
{N_{\mathrm{model}}}
\times 100\%
$$

where:

其中：

- $R_{\mathrm{adapt}}$: model deployment adaptation rate;  
  $R_{\mathrm{adapt}}$：模型部署适配率；
- $N_{\mathrm{adapted}}$: number of downstream models reaching the predefined baseline criterion;  
  $N_{\mathrm{adapted}}$：达到预定义 baseline criterion 的下游模型数量；
- $N_{\mathrm{model}}$: total number of evaluated downstream models.  
  $N_{\mathrm{model}}$：参与评价的下游模型总数。

If a tolerance threshold is used instead of the strict criterion above:

如果采用容差阈值而非上述严格判定标准，则：

$$
A_m
=
\begin{cases}
1, & \dfrac{S_{\mathrm{int},m}}{S_{\mathrm{base},m}}\geq\tau \\
0, & \text{otherwise}
\end{cases}
$$

where:

其中：

- $\tau$: predefined adaptation threshold.  
  $\tau$：预定义适配阈值。

For error metrics, where a smaller value indicates better performance, the comparison direction should be reversed.

对于误差类指标，如果数值越小表示模型性能越好，则应反向定义上述比较方向。

---

## L.4. User experience
## L.4. 用户体验

### L.4.1 Learning time
### L.4.1 学习时间

**Definition in Table 9:**  
**Table 9 中的定义：**

Average time for users to master the framework from scratch.

用户从零开始掌握该框架所需的平均时间。

For participant $i$:

对于参与者 $i$：

$$
T_{\mathrm{learn},i}
=
t_{\mathrm{master},i}
-
t_{\mathrm{start},i}
$$

where:

其中：

- $T_{\mathrm{learn},i}$: learning time of participant $i$, in hours (h);  
  $T_{\mathrm{learn},i}$：参与者 $i$ 的学习时间，单位为小时（h）；
- $t_{\mathrm{start},i}$: beginning of the standardized training procedure;  
  $t_{\mathrm{start},i}$：标准化培训过程的开始时间；
- $t_{\mathrm{master},i}$: time at which participant $i$ satisfies the predefined mastery criterion.  
  $t_{\mathrm{master},i}$：参与者 $i$ 达到预定义掌握标准的时间。

For $N$ participants:

对于 $N$ 名参与者：

$$
\overline{T}_{\mathrm{learn}}
=
\frac{1}{N}
\sum_{i=1}^{N}
T_{\mathrm{learn},i}
$$

The mastery criterion should remain identical across all compared systems.

所有被比较系统应采用完全一致的掌握判定标准。

---

### L.4.2 Task completion rate
### L.4.2 任务完成率

**Definition in Table 9:**  
**Table 9 中的定义：**

Proportion of successfully finished data integration tasks within limited time.

在规定时间内成功完成数据整合任务的比例。

The task completion rate is:

任务完成率定义为：

$$
R_{\mathrm{completion}}
=
\frac{N_{\mathrm{success}}}
{N_{\mathrm{total}}}
\times 100\%
$$

where:

其中：

- $R_{\mathrm{completion}}$: task completion rate;  
  $R_{\mathrm{completion}}$：任务完成率；
- $N_{\mathrm{success}}$: number of tasks successfully completed within the predefined time limit and satisfying all output requirements;  
  $N_{\mathrm{success}}$：在规定时间内完成且满足全部输出要求的任务数量；
- $N_{\mathrm{total}}$: total number of assigned tasks.  
  $N_{\mathrm{total}}$：分配任务总数。

A task is considered successfully completed only when both time and output-quality criteria are satisfied:

只有同时满足时间要求和输出质量要求时，任务才被判定为成功完成：

$$
I_{\mathrm{success}}
=
I_{\mathrm{time}}
\times
I_{\mathrm{quality}}
$$

where:

其中：

- $I_{\mathrm{time}}=1$ when the task is completed within the specified time limit;  
  当任务在规定时间内完成时，$I_{\mathrm{time}}=1$；
- $I_{\mathrm{quality}}=1$ when all predefined output requirements are satisfied;  
  当任务满足全部预定义输出要求时，$I_{\mathrm{quality}}=1$；
- otherwise, the corresponding indicator equals 0.  
  否则，相应指示变量取值为 0。

Therefore:

因此：

$$
N_{\mathrm{success}}
=
\sum_{i=1}^{N_{\mathrm{total}}}
I_{\mathrm{success},i}
$$

---

### L.4.3 Subjective satisfaction score
### L.4.3 主观满意度评分

**Definition in Table 9:**  
**Table 9 中的定义：**

User experience score based on a five-point Likert scale.

基于五级 Likert 量表获得的用户体验评分。

Each participant assigns a score:

每位参与者按照以下等级进行评分：

$$
x_i\in\{1,2,3,4,5\}
$$

where:

其中：

- 1 = very dissatisfied;  
  1 = 非常不满意；
- 2 = dissatisfied;  
  2 = 不满意；
- 3 = neutral;  
  3 = 一般；
- 4 = satisfied;  
  4 = 满意；
- 5 = very satisfied.  
  5 = 非常满意。

The mean satisfaction score is:

平均满意度评分为：

$$
\overline{S}_{\mathrm{sat}}
=
\frac{1}{N}
\sum_{i=1}^{N}
x_i
$$

where:

其中：

- $\overline{S}_{\mathrm{sat}}$: mean subjective satisfaction score;  
  $\overline{S}_{\mathrm{sat}}$：平均主观满意度评分；
- $x_i$: satisfaction score provided by participant $i$;  
  $x_i$：参与者 $i$ 给出的满意度评分；
- $N$: number of valid responses.  
  $N$：有效评分数量。

The corresponding standard deviation is:

对应的标准差为：

$$
SD_{\mathrm{sat}}
=
\sqrt{
\frac{
\sum_{i=1}^{N}
(x_i-\overline{S}_{\mathrm{sat}})^2
}{
N-1
}
}
$$

For a questionnaire containing $M$ items, the overall score for participant $i$ is:

对于包含 $M$ 个题项的问卷，参与者 $i$ 的总体评分定义为：

$$
S_i
=
\frac{1}{M}
\sum_{j=1}^{M}
x_{ij}
$$

where:

其中：

- $S_i$: overall satisfaction score of participant $i$;  
  $S_i$：参与者 $i$ 的总体满意度评分；
- $M$: number of questionnaire items;  
  $M$：问卷题项数量；
- $x_{ij}$: score given by participant $i$ to questionnaire item $j$.  
  $x_{ij}$：参与者 $i$ 对第 $j$ 个题项给出的评分。

The cohort-level satisfaction score is subsequently calculated from all valid $S_i$ values.

最终根据所有有效的 $S_i$ 计算用户群体层面的满意度评分。

---

## L.5. Repeated measurements and statistical aggregation
## L.5. 重复测量与统计汇总

For participant $i$ and repeated trial $r$, let $x_{ir}$ denote the measured value of a given indicator.

对于参与者 $i$ 的第 $r$ 次重复实验，令 $x_{ir}$ 表示相应评价指标的测量值。

The participant-level mean is:

参与者层面的平均值为：

$$
\overline{x}_i
=
\frac{1}{R_i}
\sum_{r=1}^{R_i}
x_{ir}
$$

where:

其中：

- $R_i$: number of valid repeated trials completed by participant $i$;  
  $R_i$：参与者 $i$ 完成的有效重复实验次数；
- $\overline{x}_i$: participant-level mean.  
  $\overline{x}_i$：参与者层面的平均值。

The cohort-level mean is:

用户群体层面的平均值为：

$$
\overline{x}
=
\frac{1}{N}
\sum_{i=1}^{N}
\overline{x}_i
$$

The cohort-level standard deviation is:

用户群体层面的标准差为：

$$
SD
=
\sqrt{
\frac{
\sum_{i=1}^{N}
(\overline{x}_i-\overline{x})^2
}{
N-1
}
}
$$

This aggregation procedure ensures that participants with different numbers of valid repeated trials do not receive unequal statistical weights.

该统计汇总方法能够避免因不同参与者有效重复实验次数不同而导致某些参与者在总体统计中获得不等权重。

---

## L.6. Relative improvement and reduction
## L.6. 相对提升率与相对降低率

The direction of the improvement metric depends on whether a larger or smaller value represents better performance.

相对性能变化的计算方向取决于指标数值越大还是越小代表更好的性能。

For indicators where **larger values indicate better performance**:

对于**数值越大越好**的指标：

$$
\eta_{\uparrow}
=
\frac{
X_{\mathrm{GenBFKit}}-X_{\mathrm{baseline}}
}{
X_{\mathrm{baseline}}
}
\times 100\%
$$

For indicators where **smaller values indicate better performance**:

对于**数值越小越好**的指标：

$$
\eta_{\downarrow}
=
\frac{
X_{\mathrm{baseline}}-X_{\mathrm{GenBFKit}}
}{
X_{\mathrm{baseline}}
}
\times 100\%
$$

where:

其中：

- $X_{\mathrm{GenBFKit}}$: metric value obtained using GenBFKit;  
  $X_{\mathrm{GenBFKit}}$：使用 GenBFKit 获得的指标值；
- $X_{\mathrm{baseline}}$: corresponding metric value obtained using the reference system;  
  $X_{\mathrm{baseline}}$：参考系统对应的指标值；
- $\eta_{\uparrow}$: relative improvement for larger-is-better indicators;  
  $\eta_{\uparrow}$：数值越大越好指标的相对提升率；
- $\eta_{\downarrow}$: relative reduction for smaller-is-better indicators.  
  $\eta_{\downarrow}$：数值越小越好指标的相对降低率。

For GenBFKit, **data integration time, single-task data access time, learning time, and query response time** are smaller-is-better indicators.

对于 GenBFKit，**data integration time、single-task data access time、learning time 和 query response time** 属于数值越小越好的指标。

**Parameter standardization rate, data integrity retention rate, cross-task data reuse rate, model deployment adaptation rate, task completion rate, and subjective satisfaction score** are larger-is-better indicators.

**Parameter standardization rate、data integrity retention rate、cross-task data reuse rate、model deployment adaptation rate、task completion rate 和 subjective satisfaction score** 属于数值越大越好的指标。