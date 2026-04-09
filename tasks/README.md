# Tasks

这里不是传统课程目录，而是模型工程工单列表。

V2 的任务体系会逐步从旧的 `T00-T32` 编号，迁移到按能力线组织的新编号:

- `P*`: Pretraining
- `S*`: Post-Training
- `C*`: Coding
- `M*`: Multimodal
- `A*`: Agentic
- `H*`: Harness

## 工单模板

每个任务文档都应采用同一模板:

- 背景
- 任务目标
- 业务与资源约束
- 代码改造点
- 交付标准
- 原理补充
- 实验步骤
- 结果解读
- 线上风险
- 复盘与延伸

## V2 任务分层

### `Track P: Pretraining`

目标:

- 理解基础模型能力从哪里来
- 理解数据、上下文和训练稳定性如何决定能力上限

建议任务:

- `P00` 最小预训练闭环
- `P01` token、batch、loss
- `P02` 上下文利用与 attention
- `P03` transformer block 拆解
- `P10` data mixture 与采样策略
- `P11` continued pretraining / domain adaptation
- `P12` context length 扩展
- `P20` 预训练失败模式复盘

### `Track S: Post-Training`

目标:

- 理解模型行为如何被后训练塑形
- 区分训练增强、推理增强和行为协议

建议任务:

- `S00` instruction tuning
- `S01` structured output
- `S02` eval pack
- `S10` reasoning trace SFT
- `S11` self-consistency 与 verifier
- `S12` rejection sampling
- `S20` toy DPO
- `S21` toy GRPO
- `S22` 后训练路线复盘

### `Track C: Coding`

目标:

- 理解代码模型的数据、上下文、执行反馈和评测特点

建议任务:

- [C00_code_completion_baseline.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/C00_code_completion_baseline.md)
- [C01_repo_context_packing.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/C01_repo_context_packing.md)
- [C02_bugfix_finetuning.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/C02_bugfix_finetuning.md)
- [C03_execution_feedback_eval.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/C03_execution_feedback_eval.md)
- [C10_coding_judge_verifier.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/C10_coding_judge_verifier.md)
- [C11_multi_file_bugfix_protocol.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/C11_multi_file_bugfix_protocol.md)
- `C12` pass@k 与 execution-based eval
- `C20` SWE-bench 风格任务拆解

### `Track M: Multimodal`

目标:

- 理解图文联合能力、多模态对齐和文档/图表理解的差异

建议任务:

- [M00_visual_qa_loop.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/M00_visual_qa_loop.md)
- [M01_document_understanding.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/M01_document_understanding.md)
- [M02_chart_reasoning.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/M02_chart_reasoning.md)
- [M03_noisy_ocr_pipeline.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/M03_noisy_ocr_pipeline.md)
- `M10` multimodal SFT
- `M11` 多模态失败模式与评测

### `Track A: Agentic`

目标:

- 理解 tool use、memory、reflection 和执行反馈如何组合成 agent 能力

建议任务:

- [A00_single_tool_loop.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/A00_single_tool_loop.md)
- [A01_multi_step_tools.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/A01_multi_step_tools.md)
- [A02_state_memory.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/A02_state_memory.md)
- [A10_failure_recovery.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/A10_failure_recovery.md)
- `A11` reflection
- `A12` agent eval
- `A20` browser / office workflow

### `Track H: Harness`

目标:

- 理解为什么很多团队最终不是卡在模型结构，而是卡在 harness 能力

建议任务:

- [H00_unified_entrypoints.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/H00_unified_entrypoints.md)
- [H01_checkpoint_config_registry.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/H01_checkpoint_config_registry.md)
- [H02_regression_harness.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/H02_regression_harness.md)
- [H03_latency_cost_profiling.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/H03_latency_cost_profiling.md)
- [H10_release_gate.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/H10_release_gate.md)
- `H20` 周报与复盘模板

## 旧任务到新任务的映射

当前仓库保留原有任务文档，作为过渡层。

映射关系:

- [T00_bootstrap.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T00_bootstrap.md) -> `P00`
- [T01_data_pipeline.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T01_data_pipeline.md) -> `P01`
- [T02_context_debug.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T02_context_debug.md) -> `P02`
- [T03_transformer_block.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T03_transformer_block.md) -> `P03`
- [T10_sft_for_assistant.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T10_sft_for_assistant.md) -> `S00`
- [T11_structured_output.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T11_structured_output.md) -> `S01`
- [T12_eval_pack.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T12_eval_pack.md) -> `S02`
- [T22_reasoning_trace_sft.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T22_reasoning_trace_sft.md) -> `S10`
- [T20_reasoning_enhancement.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T20_reasoning_enhancement.md) -> `S11`
- [T21_verifier_rerank.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T21_verifier_rerank.md) -> `S11` 子任务
- [T30_toy_dpo.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T30_toy_dpo.md) -> `S20`
- [T31_toy_grpo.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T31_toy_grpo.md) -> `S21`
- [T32_alignment_review.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/T32_alignment_review.md) -> `S22`

## 编写要求

V2 的任务文档要避免三种写法:

- 纯知识点罗列，没有代入感
- 纯产品故事，没有代码与实验抓手
- 纯 demo 演示，没有指标、失败模式和工程取舍

理想状态是读者读完一个任务后，会自然产生这些判断:

1. 为什么团队现在要做这件事
2. 改哪段代码最关键
3. 哪些指标说明真的变好了
4. 哪些现象只是表面提升
5. 在不同团队条件下，这条路线是否值得继续
