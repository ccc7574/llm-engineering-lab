# Track A: Agentic

这个能力线负责解释 agent 能力如何由模型、工具、状态管理和环境反馈共同组成。

重点问题:

- tool use 与 prompt chaining 的区别
- planner、executor、memory、reflection 各自解决什么问题
- 为什么 agent eval 不能只看最终答案

当前状态:

- V2 规划已建立
- 已有 `tiny_agentic`、`tiny_agentic_memory` 数据、工具定义、state 对象、task runner 和 `eval/agentic_eval.py`
- 已形成 direct vs tool_use 的最小 agentic 对照实验
- 已形成 tool_use vs stateful 的 state / recovery 对照实验

建议首批任务:

- `A00` 单工具调用
- `A01` 多步工具链
- `A02` memory 与状态管理
- `A10` 失败恢复

当前可直接运行的最小命令见 [runbook.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/runbook.md)。
