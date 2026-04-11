# Track S: Post-Training

这个能力线负责解释模型行为如何在预训练之后被重新塑形。

重点问题:

- 为什么 base model 不等于 instruction model
- SFT 改了什么
- reasoning trace、verifier、preference optimization 分别解决什么问题
- 为什么很多“模型变聪明”其实是协议、数据和筛选机制变化

建议任务:

- [S00_instruction_tuning.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S00_instruction_tuning.md)
- [S01_structured_output_and_protocol.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S01_structured_output_and_protocol.md)
- [S02_minimal_eval_pack.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S02_minimal_eval_pack.md)
- [S10_reasoning_trace_sft.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S10_reasoning_trace_sft.md)
- [S11_self_consistency_and_verifier.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S11_self_consistency_and_verifier.md)
- [S12_rejection_sampling_route.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S12_rejection_sampling_route.md)
- [S20_toy_dpo.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S20_toy_dpo.md)
- [S21_toy_grpo.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S21_toy_grpo.md)
- [S22_post_training_review.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S22_post_training_review.md)
- [S23_alignment_eval_and_visualization.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/S23_alignment_eval_and_visualization.md)

当前仓库中最直接相关的实现:

- [stage2_sft](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage2_sft)
- [stage3_reasoning](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage3_reasoning)
- [stage4_verifier](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage4_verifier)
- [stage5_toy_alignment](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage5_toy_alignment)

当前主要缺口:

- 当前最主要剩余缺口已经转到更深的 multimodal SFT / browser workflow，而不是 post-training 基础 runnable

当前已补到:

- `S12` rejection sampling 已补到 runnable 筛选 / accepted dataset 导出
- `S20-S21` 已有 toy runnable 入口
- 已形成 base vs `DPO`、base vs `GRPO-like` 的 alignment eval / regression 对照
- 已把 alignment 结果接进 summary board，可直接看 chosen win rate、preference margin 和 drift
