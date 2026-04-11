# A12: 用 planner / observer 把 agent 草稿升级成可审计的生产输出

## 背景

真实团队里的 agent 失败，很多时候不是“不会调用工具”，而是:

- 没先把任务拆成必须完成的步骤
- 执行完后没有 observer 去检查策略边界
- 草稿看起来合理，但最终输出仍然不满足 escalation / approval / safety 要求

这类问题只靠 state 或 reflection 往往不够，因为团队需要的是可审计的 workflow，而不是偶尔修对一次。

参考图:

- [agentic_planner_observer_loop.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/agentic_planner_observer_loop.svg)

## 任务目标

- 新增 planner / observer 级 agent 数据集
- 增加 `stateful` 对 `planner_observer` 的明确对照
- 让系统必须先做 plan，再执行，再通过 observer check 决定是否 reroute / repair

## 交付标准

- 至少有一组需要 escalation-safe reroute 的任务
- 至少有一组需要 threshold / policy check 的任务
- 至少记录 `avg_planning_steps` 和 `avg_observer_checks`
- 至少把新路线接入统一 eval 与 regression suite
