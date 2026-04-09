# A00: 跑通单工具调用闭环，理解 agent 不是普通 prompt chaining

## 背景

很多团队第一次做 agent 时，会把它理解成“让模型多说几步”。但真实工程里，agent 的关键区别是它会显式调用工具，而不是只在文本里假装自己做了事。

## 任务目标

- 建立单工具调用的最小闭环
- 让读者看到 direct answer 和 tool-based answer 的区别
- 给后续多步 agent 流程建立最小基线

## 业务与资源约束

- 工具必须简单、可重复
- 任务必须能单机离线运行
- 优先先展示机制，不追求复杂任务

## 代码改造点

- `code/stage_agentic/`
- `datasets/tiny_agentic/`
- `eval/agentic_eval.py`

## 交付标准

- 至少定义一种工具调用任务
- 至少提供 direct 与 tool_use 两种策略对照
- 至少记录工具调用次数和任务成功率

## 原理补充

单工具闭环最关键的认知是:

1. agent 的能力不只来自语言生成
2. 工具提供外部行动能力
3. 评测必须同时看结果和过程

## 实验步骤

1. 选择一个必须借助工具才能稳定完成的任务
2. 跑 direct 策略
3. 跑 tool_use 策略
4. 比较 task success rate 与 tool_calls

## 结果解读

读者应该知道:

- tool use 是 agent 能力的起点
- 没有工具调用的“agent”很多时候只是更长的 prompt

## 线上风险

- 工具返回值不稳定
- 工具 schema 不清晰，模型调用错误
- 团队只看最终答案，不看工具使用成本
