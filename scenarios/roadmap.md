# Roadmap

这个文件保留为过渡入口。

`LLM Engineering Lab` 的主路线已经从原来的“内部 AI 助手演练”切换为 V2 的“模型工程实验室”路线。

## 现在应该看哪里

请优先阅读:

1. [docs/project_charter.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/project_charter.md)
2. [docs/roadmap_v2.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/roadmap_v2.md)
3. [docs/learning_paths.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/learning_paths.md)
4. [tasks/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/README.md)

## V1 到 V2 的变化

旧路线的核心问题是:

- 主叙事过于聚焦“内部 AI 助手”
- 任务体系主要覆盖预训练内核与基础后训练
- 对 coding、多模态、agentic、harness 的覆盖不足
- 不足以支撑“面向 2026 真实模型工程工作”的学习目标

V2 的改动方向是:

- 从单一产品故事，升级为 6 条能力线
- 从 sprint 叙事，升级为工单加案例层
- 从单一路线，升级为 Starter / Practitioner / Production-minded 三层学习路径
- 从“小团队视角”，升级为大厂、中型公司、小团队三类约束并行

## V2 核心能力线

- `Pretraining`
- `Post-Training`
- `Coding`
- `Multimodal`
- `Agentic`
- `Harness`

## 现有内容如何对接 V2

当前仓库中已实现的部分，主要对应:

- `stage0_bigram`、`stage1_nanogpt_core` -> `Pretraining`
- `stage2_sft`、`stage3_reasoning`、`stage4_verifier` -> `Post-Training`

尚未完成但将在 V2 中补齐:

- `Coding`
- `Multimodal`
- `Agentic`
- `Harness`
- `stage5_toy_alignment`

## 近期执行顺序

1. 重写入口文档和任务总览
2. 稳定 `Pretraining` 与 `Post-Training` 的 golden path
3. 补 `Coding` 与 `Harness` 任务骨架
4. 再扩 `Multimodal` 与 `Agentic`

如果你是仓库的新读者，不建议再沿着旧版 sprint 文本理解整个项目，而应直接以 V2 文档为准。
