# Track P: Pretraining

这个能力线负责解释基础模型能力从哪里来。

重点问题:

- tokenization 改了什么
- next-token prediction 为什么有效
- attention 与上下文是如何形成能力的
- 数据分布、continued pretraining、context length 如何影响上限

建议任务:

- [P00_minimal_pretraining_loop.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P00_minimal_pretraining_loop.md)
- [P01_token_batch_loss.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P01_token_batch_loss.md)
- [P02_context_usage_and_attention.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P02_context_usage_and_attention.md)
- [P03_transformer_block_dissection.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P03_transformer_block_dissection.md)
- [P10_data_mixture_and_sampling.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P10_data_mixture_and_sampling.md)
- [P11_continued_pretraining_and_domain_adaptation.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P11_continued_pretraining_and_domain_adaptation.md)
- [P12_context_length_extension.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P12_context_length_extension.md)
- [P20_pretraining_failure_review.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P20_pretraining_failure_review.md)

当前仓库中最直接相关的实现:

- [stage0_bigram](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage0_bigram)
- [stage1_nanogpt_core](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage1_nanogpt_core)
- `train_mixture.py` 已可比较 uniform vs domain-heavy 数据混合
- `continue_pretraining.py` 已可比较 domain adaptation 前后领域 loss

当前主要缺口:

- `P10-P11` 已有 runnable 专项脚本，但仍然是教学级最小实现
- context extension 目前更多依赖已有训练脚本参数实验
