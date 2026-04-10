# A11: 给 agent 补 reflection 与 task-level eval

## 背景

很多 agent 不是真的不会做，而是第一版草稿不可靠。如果没有显式 reflection，它会把错误草稿直接输出；如果没有 eval，团队也很难知道 reflection 到底是在省错还是在白白增加步骤。

## 任务目标

- 增加 `draft -> critique -> revise` 的最小反思链
- 增加 reflection 相关指标
- 让 reflection 能进入 regression suite

## 交付标准

- 至少有一个任务会因为缺少 reflection 而失败
- 至少记录 `reflection_steps`
- 至少有 `tool_use` vs `reflective` 对照评测
