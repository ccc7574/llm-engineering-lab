# Project Charter

## 项目一句话

`LLM Engineering Lab` 是一个面向非算法工程师的沉浸式模型工程实验室，用真实研发工单把模型的预训练、后训练、coding、多模态、agentic 与 harness 工程串成一条由浅入深的学习主线。

## 为什么做这个项目

很多工程师已经在工作里频繁接触模型，但仍然存在几个普遍问题:

- 知道怎么调用模型，却不知道模型能力为什么这样形成
- 知道要做 SFT、RAG 或 agent，却不知道这些方法分别改了什么
- 能跑 demo，却缺少评测、回归、成本和风险意识
- 很难把“模型原理”和“真实团队工程决策”连接起来

这个项目的目标，就是把这些断点补上。

## 目标

- 让非算法背景工程师看懂并跑通最小模型工程闭环
- 让读者理解模型能力如何从训练、后训练和推理策略中逐步形成
- 让学习过程尽量贴近 2026 年真实模型团队的工作方式
- 让工程师能用实验、指标和工单语言讨论模型优化，而不是只谈抽象概念
- 让不同规模团队都能在仓库中找到适合自己的路线

## 非目标

- 不追求复现超大规模训练系统
- 不追求成为通用生产平台
- 不追求覆盖所有模型论文和所有热门方向
- 不把“调通一个 demo”误认为“掌握模型工程”

## 目标读者

- 有后端、平台、数据、应用、客户端背景的工程师
- 能看懂代码、理解系统约束，但不是算法研究员
- 希望从真实工作视角理解模型能力优化的人
- 希望将模型工程方法迁移到业务场景的人

## 项目结构观

V2 以 6 条能力线组织内容:

- `Pretraining`
- `Post-Training`
- `Coding`
- `Multimodal`
- `Agentic`
- `Harness`

同时叠加 3 类公司规模案例层:

- `bigtech`
- `mid_company`
- `small_team`

## 方法论

项目采用以下方法论:

- `工单驱动`: 用真实任务而不是抽象章节推进学习
- `由浅入深`: 每条能力线都分为 Starter、Practitioner、Production-minded
- `Eval First`: 先定义指标和样本，再改训练或推理链路
- `Harness First`: 把训练、评测、推理、追踪、回归放进统一工程视角
- `案例分层`: 同一方法明确区分不同公司规模下的合理解法

## 成功标准

如果项目达到以下状态，说明它开始具备真正的交付价值:

- 新读者可以沿着一条 Starter 路径独立完成第一轮学习
- 读者能把原理映射到代码、实验和指标，而不是停留在术语层
- 至少 12 个任务形成 `文档 + 代码 + 数据 + eval` 闭环
- 读者能说清楚 SFT、verifier、偏好优化、tool use、harness 各自解决什么问题
- 大厂、中型公司、小团队三类案例都有明确的约束与取舍说明

## 当前阶段

当前仓库已经具备六条能力线的最小底座，但还没有完成整个 V2:

- 已有最小实现: `stage0_bigram`、`stage1_nanogpt_core`、`stage2_sft`、`stage3_reasoning`、`stage4_verifier`、`stage_coding`、`stage_multimodal`、`stage_agentic`、`stage_harness`
- 已补齐 `stage5_toy_alignment`，并补出 `P10/P11`、`M10` 等 runnable 路线
- 仍待补强: `Pretraining` 更强的 context extension 专项、`M11` failure pack、`A20` browser/office workflow 的 runnable 深化，以及更完整的 production-minded 案例层

因此，当前最重要的工作不是继续扩散主题，而是把现有 starter path 推到更稳定的 golden path、回归面板和真实工作流形态。
