# Track S: Post-Training

这个能力线负责解释模型行为如何在预训练之后被重新塑形。

重点问题:

- 为什么 base model 不等于 instruction model
- SFT 改了什么
- reasoning trace、verifier、preference optimization 分别解决什么问题
- 为什么很多“模型变聪明”其实是协议、数据和筛选机制变化

建议任务:

- `S00` 到 `S02`
- `S10` 到 `S12`
- `S20` 到 `S22`

当前仓库中最直接相关的实现:

- [stage2_sft](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage2_sft)
- [stage3_reasoning](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage3_reasoning)
- [stage4_verifier](/Volumes/ExtaData/newcode/llm-engineering-lab/code/stage4_verifier)
