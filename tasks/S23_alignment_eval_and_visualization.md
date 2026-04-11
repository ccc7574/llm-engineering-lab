# S23: 把 toy alignment 训练接成可比较的 eval / regression / visualization 闭环

## 背景

有了 `S20-S21` 的训练脚本之后，团队下一步不会只问“能不能跑起来”，而会问:

- base checkpoint 和 aligned checkpoint 到底差了多少
- chosen / rejected 偏好到底有没有真的被拉开
- alignment 收益是否值得额外的 KL 偏移和工程复杂度

如果没有统一 eval 和对照 artifact，alignment 仍然只是训练日志，不是工程决策依据。

参考图:

- [post_training_alignment_loop.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/post_training_alignment_loop.svg)

## 任务目标

- 新增 alignment eval，能比较 base / DPO / GRPO-like checkpoint
- 把对照结果接进 regression suite 和 summary board
- 让产物直接回答 chosen win rate、preference margin 和 KL drift 的变化

## 交付标准

- 至少输出 `policy_chosen_win_rate`
- 至少输出 `mean_preference_margin`
- 至少输出对 reference 的 drift 指标
- 至少把 `DPO` 和 `GRPO-like` 两条路线接入统一 regression suite
