# Track P: Pretraining

这个能力线负责解释基础模型能力从哪里来。

重点问题:

- tokenization 改了什么
- next-token prediction 为什么有效
- attention 与上下文是如何形成能力的
- 数据分布、continued pretraining、context length 如何影响上限

建议任务:

- `P00` 到 `P03`
- `P10` 到 `P12`
- `P20`

当前仓库中最直接相关的实现:

- [stage0_bigram](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage0_bigram)
- [stage1_nanogpt_core](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage1_nanogpt_core)
