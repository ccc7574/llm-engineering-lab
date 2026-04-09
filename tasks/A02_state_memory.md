# A02: 给 agent 补最小状态管理，理解 memory 不是“多存点字”

## 背景

随着工具链变长，agent 很快会遇到一个问题: 前面步骤拿到的信息，后面如何稳定使用? 这就是状态管理和 memory 的最小问题形态。

## 任务目标

- 理解 agent state 和普通上下文拼接的区别
- 为后续 reflection、error recovery 打基础
- 让读者知道什么时候应该显式维护状态

## 业务与资源约束

- 先不做长期记忆
- 先聚焦单任务会话内的状态传递
- 必须让状态结构清晰、可调试

## 代码改造点

- `code/stage_agentic/task_runner.py`
- `code/stage_agentic/state.py`
- `eval/agentic_eval.py`

## 交付标准

- 至少定义一个显式状态对象或 trace 结构
- 至少展示状态如何在步骤间传递
- 至少说明状态丢失会导致什么失败
- 至少能在评测里看到 `state_reads` / `state_writes`

## 原理补充

对工程师来说，memory 最重要的不是“记更多”，而是:

1. 记住什么
2. 如何结构化保存
3. 哪一步消费这些状态

## 结果解读

这一单结束后，读者应该知道:

- memory 是 agent 工程问题的一部分
- 状态结构设计会直接影响 agent 可靠性
