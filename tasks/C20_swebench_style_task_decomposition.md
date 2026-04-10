# C20: 做 SWE-bench 风格任务拆解

## 背景

真实代码代理的难点往往不是“能不能改一行代码”，而是:

- issue 文本并不直接告诉你根因在哪
- failing test output 只是线索，不是答案
- 入口文件和真正要修的共享模块可能不是同一个

这正是 SWE-bench 风格任务的核心。

参考图:

- [coding_eval_ladder.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/coding_eval_ladder.svg)

## 任务目标

- 建立 `issue_localized -> triage_loop` 对照
- 让任务同时包含 issue 文本、失败测试线索和跨文件修复
- 让 triage / localization / patch repair 进入统一评测

## 交付标准

- 至少有一个共享工具函数才是真正根因的任务
- 至少记录 `avg_triage_reads`
- 至少输出 `relevant_context_recall` 与 `patch_recall`
- 至少接入 regression suite
