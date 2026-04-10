# Learning Paths

## 说明

这个文件把 `LLM Engineering Lab` V2 的内容按学习目标重新组织。

如果 `roadmap_v2.md` 解决的是“项目要建设什么”，那么这个文件解决的是“读者应该怎么学”。

## 路径 1: Core Intuition

适合:

- 第一次系统接触模型工程的工程师
- 希望先建立直觉，再进入更复杂优化的人

目标:

- 跑通最小训练与评测闭环
- 理解 token、loss、上下文、SFT 的基本作用
- 能解释模型为什么会表现成这样

建议顺序:

1. `P00`
2. `P01`
3. `P02`
4. `P03`
5. `S00`
6. `S01`
7. `S02`
8. `H00`

当前可直接对应的现有任务:

- [P00_minimal_pretraining_loop.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P00_minimal_pretraining_loop.md)
- [P01_token_batch_loss.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P01_token_batch_loss.md)
- [P02_context_usage_and_attention.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P02_context_usage_and_attention.md)
- [P03_transformer_block_dissection.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P03_transformer_block_dissection.md)
- [S00_instruction_tuning.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S00_instruction_tuning.md)
- [S01_structured_output_and_protocol.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S01_structured_output_and_protocol.md)
- [S02_minimal_eval_pack.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S02_minimal_eval_pack.md)

## 路径 2: Capability Optimization

适合:

- 已经能跑通最小链路
- 希望理解能力增强方法和实验设计的人

目标:

- 掌握预训练阶段的关键可调因素
- 理解 reasoning、verifier、coding、多模态、tool use 等能力如何增强
- 会做小规模评测和对照实验

建议顺序:

1. `P10`
2. `P11`
3. `P12`
4. `S10`
5. `S11`
6. `S12`
7. `C00-C03`
8. `M00-M02`
9. `A00-A02`
10. `H01-H03`

当前仓库中已经有最小底座的部分:

- [P10_data_mixture_and_sampling.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P10_data_mixture_and_sampling.md)
- [P11_continued_pretraining_and_domain_adaptation.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P11_continued_pretraining_and_domain_adaptation.md)
- [P12_context_length_extension.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P12_context_length_extension.md)
- [S10_reasoning_trace_sft.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S10_reasoning_trace_sft.md)
- [S11_self_consistency_and_verifier.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S11_self_consistency_and_verifier.md)
- [S12_rejection_sampling_route.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S12_rejection_sampling_route.md)
- 其中 `S20-S21` 路线的代码实现仍待补齐

## 路径 3: Production-Minded Engineering

适合:

- 要在真实团队里承担模型工程职责的人
- 需要做路线判断、成本权衡和回归管理的人

目标:

- 能从收益、成本、风险三方面评估方案
- 能根据不同公司规模约束做技术取舍
- 能为模型上线和持续迭代制定标准

建议顺序:

1. `P20`
2. `S20-S22`
3. `C10-C20`
4. `M10-M11`
5. `A10-A20`
6. `H10-H20`

## 按角色推荐

### 后端 / 平台工程师

建议优先:

- `P00-P03`
- `S00-S02`
- `H00-H03`
- `A00-A02`

### 应用 / 产品工程师

建议优先:

- `S00-S12`
- `A00-A20`
- `H00-H03`
- `M00-M02`

### 数据 / MLE / 模型平台工程师

建议优先:

- `P00-P20`
- `S00-S22`
- `H00-H20`
- `C10-C20`

### AI Coding / Agent 产品工程师

建议优先:

- `C00-C20`
- `A00-A20`
- `S10-S12`
- `H01-H03`

## 按公司规模推荐

### 大厂

建议重点:

- `P10-P20`
- `S20-S22`
- `C10-C20`
- `H00-H20`

### 中型 AI 公司

建议重点:

- `S00-S12`
- `C00-C10`
- `A00-A10`
- `H00-H10`

### 小团队

建议重点:

- `S00-S11`
- `A00-A02`
- `H00-H03`
- `C00-C03`

## 当前建议的第一批可交付学习路径

为了尽快让仓库具备教学交付价值，第一批建议优先完成:

1. `Core Intuition` 全链路
2. `Capability Optimization` 中的 `S10-S11`
3. `Capability Optimization` 中的 `C00-C03` 骨架
4. `Capability Optimization` 中的 `H01-H03` 骨架

完成这批后，项目就会从“有局部实现”进入“有完整学习路径”状态。
