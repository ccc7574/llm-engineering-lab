# C13: 把代码修复升级成会检索、会跑测、会自修复的 agentic coding loop

## 背景

真实一线 AI 公司的 coding agent 很少是“看一眼文件就直接给最终答案”。

更常见的流程是:

- 先读入口文件和 issue
- 产出第一版 patch
- 跑测试或最小验证
- 根据失败信号继续读仓库
- 修第二版 patch 再提交

## 任务目标

- 建立最小 `single_pass -> repair_loop` 对照
- 把 repo retrieval、patch proposal、test execution feedback 串成一条闭环
- 让读者理解为什么编码代理的关键不只是 patch 质量，还有失败后的恢复能力

## 交付标准

- 至少有一组需要跨文件修复的 agentic coding 任务
- 至少记录 `repo_reads`、`test_runs`、`patch_attempts`、`repair_attempts`
- 至少记录 `relevant_context_recall` 与 `patch_recall`
- 至少输出 `task_success_rate` 和 `recovery_success_rate`
