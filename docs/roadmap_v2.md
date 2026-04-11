# Roadmap V2

## 一句话定位

`LLM Engineering Lab` V2 不再把自己定义为“最小内部 AI 助手演练仓库”，而是一个面向非算法工程师的沉浸式模型工程实验室。

读者的身份不再是“旁观教程的学生”，而是“2026 年加入模型团队的新工程师”，需要在真实约束下逐步理解、优化、评测和落地模型能力。

---

## 核心目标

- 让非算法工程师理解模型能力是如何被训练、后训练、评测和工程化出来的
- 让学习过程尽量贴近真实工作要求，而不是停留在概念讲解
- 让读者能在小规模实验中看懂核心原理，并把方法迁移到实际项目
- 覆盖一线 AI 大公司、中型 AI 公司、小型 AI 团队在模型工程上的不同取舍

## 非目标

- 不追求复现超大规模 SOTA 训练系统
- 不追求做通用生产平台替代品
- 不追求把所有热门方向都铺满一遍
- 不把“会调 prompt”误当成“掌握模型工程”

---

## V2 设计原则

### 1. 沉浸式工单驱动

每个模块都以真实工作单推进，而不是按章节灌输概念。

每个工单固定包含:

1. 背景
2. 任务目标
3. 业务与资源约束
4. 代码入口
5. 实验步骤
6. 指标与验收标准
7. 线上风险
8. 复盘与延伸

### 2. 由浅入深

每条能力线都分成三层:

- `Starter`: 建立直觉，跑通最小闭环
- `Practitioner`: 理解关键机制，能做针对性优化
- `Production-minded`: 能从真实团队约束出发做取舍和复盘

### 3. Eval First

先定义任务、样本、grader、回归指标，再改训练或推理链路。

### 4. Harness First

训练、评测、推理、实验记录、checkpoint 管理、回归检查都要放到统一 harness 视角下理解。

### 5. 公司规模差异显式化

同一个能力点，要明确:

- 大厂怎么做
- 中型公司怎么做
- 小团队怎么做

### 6. 原理必须落到代码和实验

所有概念都要尽量映射到:

- 一段最小代码
- 一次对照实验
- 一组指标
- 一个真实失败案例

---

## V2 总体结构

```text
llm-engineering-lab/
  README.md
  docs/
    project_charter.md
    roadmap_v2.md
    runbook.md
    learning_paths.md
  tracks/
    pretraining/
    post_training/
    coding/
    multimodal/
    agentic/
    harness/
  cases/
    bigtech/
    mid_company/
    small_team/
  tasks/
    P*/
    S*/
    C*/
    M*/
    A*/
    H*/
  code/
    ...
  eval/
    ...
  datasets/
    ...
```

说明:

- `tracks/` 负责能力线设计
- `tasks/` 负责具体工单
- `cases/` 负责不同公司规模下的真实约束映射

---

## 六条能力线

## Track P: Pretraining

目标:

- 理解基础模型能力从哪里来
- 看懂 tokenizer、数据、上下文长度、训练稳定性如何影响能力边界
- 建立“小实验不能等于真实大模型，但可以解释关键机制”的认知

学习重点:

- tokenizer 与数据分布
- next-token prediction 的真实含义
- transformer block 与 context usage
- data mixture / curriculum / domain adaptation
- context length 扩展
- scaling 的工程直觉
- continued pretraining

建议任务编号:

- `P00` 跑通最小预训练闭环
- `P01` 看懂 token、batch、loss
- `P02` 证明模型在利用上下文
- `P03` 拆解 transformer block
- `P10` 设计数据混合与采样策略
- `P11` 做 continued pretraining / domain adaptation
- `P12` 做 context length 扩展实验
- `P20` 预训练阶段的稳定性与失败模式复盘

## Track S: Post-Training

目标:

- 理解模型行为是如何被后训练塑形的
- 区分能力提升、行为塑形、推理时增强三者
- 看懂 SFT、trace、verifier、偏好优化各自改变了什么

学习重点:

- prompt template 与交互协议
- label mask 与 supervision design
- reasoning trace
- verifier / reranker
- rejection sampling
- preference optimization
- safety / style / refusal / stability

建议任务编号:

- `S00` 把 base model 变成 instruction model
- `S01` 结构化输出与协议稳定性
- `S02` 最小 eval pack
- `S10` reasoning trace SFT
- `S11` self-consistency 与 verifier
- `S12` rejection sampling 路线
- `S20` toy DPO
- `S21` toy GRPO / reward-guided update
- `S22` 后训练收益、成本、风险复盘

## Track C: Coding

目标:

- 让工程师理解代码模型为什么难、为什么值钱、为什么特别依赖数据与评测
- 让读者能围绕代码补全、bugfix、repo-level understanding 做最小实验

学习重点:

- code completion 与 infill
- repo context construction
- bug fixing
- unit test generation
- execution feedback
- self-repair
- code benchmark 设计

建议任务编号:

- `C00` 代码补全最小基线
- `C01` repo-level context packing
- `C02` bugfix 任务微调
- `C03` test generation 与执行反馈
- `C10` coding verifier / judge
- `C11` multi-file patch protocol
- `C12` test generation
- `C13` agentic coding loop
- `C20` SWE-bench 风格任务拆解
- `C21` pass@k 与 candidate sampling

## Track M: Multimodal

目标:

- 让读者理解多模态不是“多接一个编码器”这么简单
- 理解图文对齐、文档理解、图表推理、视觉 grounding 的核心差异

学习重点:

- 图文输入格式
- OCR vs document understanding
- chart/table reasoning
- visual grounding
- multimodal instruction tuning
- multimodal eval

建议任务编号:

- `M00` 图像描述与图文问答最小闭环
- `M01` 文档 OCR 与结构理解
- `M02` 图表/表格推理
- `M05` document workflow pipeline
- `M10` multimodal SFT
- `M11` 视觉失败模式与评测

## Track A: Agentic

目标:

- 让工程师理解 agent 能力来自模型、工具、状态管理和环境反馈的组合
- 避免把 agent 简化成 prompt chaining

学习重点:

- tool use / function calling
- planner-executor
- memory
- reflection
- error recovery
- approval / permission
- browser / code / office task integration

建议任务编号:

- `A00` 单工具调用闭环
- `A01` 多步工具链
- `A02` memory 与状态管理
- `A10` 失败恢复与 reflection
- `A11` agent eval / task success / step efficiency
- `A20` office workflow / browser workflow 案例

## Track H: Harness

目标:

- 让工程师理解为什么团队最终会被 harness 能力限制，而不是只被模型结构限制
- 建立实验管理、评测回归、吞吐成本、数据版本化的工程意识

学习重点:

- dataset registry
- run config
- experiment tracking
- checkpoint registry
- eval runner
- latency / throughput / cost
- regression gate
- release criteria

建议任务编号:

- `H00` 统一训练与评测入口
- `H01` checkpoint 与 config 管理
- `H02` regression eval harness
- `H03` latency / token / cost profiling
- `H10` 线上灰度与回滚标准
- `H20` 模型工程周报与复盘模板

---

## 三层学习路径

## Layer 1: Core Intuition

适合第一次接触模型工程的工程师。

目标:

- 能跑通基本链路
- 能理解最关键的原理
- 能解释模型为什么表现成这样

建议覆盖:

- `P00-P03`
- `S00-S02`
- `H00`

## Layer 2: Capability Optimization

适合已经能跑通最小链路，希望理解能力增强方法的工程师。

目标:

- 会做最小微调和对照实验
- 能围绕特定能力做定向优化
- 能读懂结果，不被表面现象误导

建议覆盖:

- `P10-P12`
- `S10-S12`
- `C00-C03`
- `M00-M02`
- `A00-A02`
- `H01-H03`

## Layer 3: Production-Minded Engineering

适合要把模型接入真实团队工作流的工程师。

目标:

- 能做收益/成本/风险权衡
- 能制定验收标准与回归门槛
- 能区分不同团队条件下的合理路线

建议覆盖:

- `P20`
- `S20-S22`
- `C10-C20`
- `M10-M11`
- `A10-A20`
- `H10-H20`

---

## 三类公司案例层

## `cases/bigtech`

特点:

- 大规模数据与算力
- 平台化训练和评测
- 更严格的安全、灰度、治理和回归体系

重点任务:

- data mixture / scaling / eval infra
- coding 与 multimodal 的大规模 benchmark
- alignment / safety / release gate

## `cases/mid_company`

特点:

- 有一定训练和微调能力
- 更强调成本收益和业务落地速度
- 往往采用开源模型加定制优化

重点任务:

- domain adaptation
- task-specific post-training
- coding / agentic / multimodal 的垂直能力增强
- latency / cost / quality 三角平衡

## `cases/small_team`

特点:

- 算力和数据都有限
- 更依赖 API、蒸馏、小规模微调和 workflow 设计
- 目标是最快做出有价值结果

重点任务:

- 小数据 SFT
- verifier / rerank
- tool use
- harness 与回归
- 快速试错与低成本上线

---

## 任务设计规范

每个任务都必须明确以下内容:

- 你为什么现在要做这件事
- 如果不做，会出现什么真实问题
- 改哪段代码最关键
- 哪些指标说明真的变好了
- 哪些指标只是幻觉
- 哪些线上风险会在真实系统里放大

每个任务都应该至少附带:

- 1 个可执行命令
- 1 个最小样本集
- 1 个对照实验
- 1 个失败案例
- 1 个面向大厂/中厂/小团队的取舍说明

---

## 2026 导向的评测要求

V2 不把评测做成“只有一个准确率数字”的样子，而是分层设计:

### 1. Capability Metrics

- loss
- exact match
- format success rate
- pass@k
- task success rate
- visual QA accuracy

### 2. Process Metrics

- average generated tokens
- sampled candidates
- tool calls
- step count
- verifier calls
- reasoning trace length

### 3. Engineering Metrics

- latency
- throughput
- token cost
- GPU hours
- memory usage
- checkpoint size

### 4. Reliability Metrics

- regression rate
- failure mode distribution
- schema violation rate
- tool error recovery rate
- unsafe / policy-violating output rate

---

## 对现有仓库内容的迁移方案

当前已有内容可这样迁移:

- 现有 `stage0_bigram`、`stage1_nanogpt_core`
  - 迁入 `Track P`
- 现有 `stage2_sft`、`stage3_reasoning`、`stage4_verifier`
  - 迁入 `Track S`
- 现有 `eval/`
  - 逐步迁入 `Track H`
- 现有 `tasks/T00-T32`
  - 逐步改造为 `P*`、`S*` 编号体系

建议对应关系:

- `T00 -> P00`
- `T01 -> P01`
- `T02 -> P02`
- `T03 -> P03`
- `T10 -> S00`
- `T11 -> S01`
- `T12 -> S02`
- `T20 -> S11`
- `T21 -> S11` 或拆成独立 verifier 子任务
- `T22 -> S10`
- `T30 -> S20`
- `T31 -> S21`
- `T32 -> S22`

---

## 建议的执行顺序

## P0: 先重写定位，不急着铺新代码

优先修改:

- `README.md`
- `docs/project_charter.md`
- `scenarios/roadmap.md` 或替换为新入口
- `tasks/README.md`

目标:

- 把项目主叙事改成“模型工程实验室”
- 明确 6 条能力线
- 明确沉浸式工单写法

## P1: 补强现有最有价值的三条线

优先建设:

- `Track S: Post-Training`
- `Track C: Coding`
- `Track H: Harness`

原因:

- 这三块最容易让非算法工程师直接联想到实际工作
- 也是最容易形成“原理 + 实践 + 工程取舍”闭环的部分

## P2: 扩展多模态与 agentic

建设:

- `Track M`
- `Track A`

要求:

- 先定义 eval 与任务成功标准
- 再做工具、链路和案例

---

## V2 的完成标准

V2 至少应达到以下状态:

- 每条能力线至少有一条 `Starter` 路径
- 至少 12 个任务达到“文档 + 代码 + 数据 + eval”闭环
- 至少 3 个完整案例，分别对应大厂、中型公司、小团队
- 至少 1 套统一 harness 能支撑回归评测
- 至少 1 条 coding 路径、1 条 multimodal 路径、1 条 agentic 路径可运行

---

## 近期建议

最合理的短期落地顺序:

1. 用本文件作为新总纲
2. 重写 `README.md` 和 `project_charter.md`
3. 把现有 `T00-T32` 重命名或映射到 `P*` / `S*`
4. 新增 `Track C` 与 `Track H` 的任务骨架
5. 在后训练链路中补出至少一个“有真实提升”的 golden path

这一步完成后，项目才会从“有想法的 toy lab”变成“有体系的模型工程学习仓库”。
