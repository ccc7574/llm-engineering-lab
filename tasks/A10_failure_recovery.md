# A10: 给 agent 补失败恢复，理解为什么“会调用工具”还不够

## 背景

很多 agent 在 demo 里看起来已经能调用工具，但一进真实流程就会遇到脏输入、非法状态、无效渠道、缺字段这些问题。没有 recovery，agent 只是会失败得更快。

## 任务目标

- 理解 recovery 和普通多步工具调用的区别
- 让读者看到非法中间状态如何触发 fallback
- 把 state 与 recovery 放进同一条最小执行链

## 业务与资源约束

- 先不做复杂 planner
- 先聚焦单会话内的失败检测与 fallback
- 必须让恢复动作可以被 trace 和指标观察到

## 代码改造点

- `code/stage_agentic/task_runner.py`
- `code/stage_agentic/state.py`
- `eval/agentic_eval.py`

## 交付标准

- 至少有一个任务会因为缺少 recovery 而失败
- 至少有一个策略可以显式记录 recovery attempt
- 至少能在评测里看到 recovery 与 success rate 的关系

## 原理补充

工程上，recovery 不是“补一个 if”这么简单，而是三件事一起成立:

1. 检测当前状态是否可继续执行
2. 决定应该回退、重试还是切换 fallback
3. 把恢复后的状态重新写回可消费的 memory

## 实验步骤

1. 跑 `tool_use`，观察遇到非法 channel 时的失败
2. 跑 `stateful`，观察 fallback 到默认升级渠道
3. 比较 `task_success_rate` 与 `avg_recovery_attempts`

## 结果解读

这一单结束后，读者应该知道:

- agent 的稳定性来自状态与恢复机制，不来自“多调几个工具”
- recovery 是可以被评测和回归的，而不是隐式逻辑
