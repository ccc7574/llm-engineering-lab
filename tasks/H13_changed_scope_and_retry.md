# H13: 让 regression suite 支持 changed-scope 和 flaky retry

## 背景

当回归套件变长之后，团队会遇到两个非常现实的问题:

- 不是每个 PR 都值得跑全量 suite
- 偶发失败如果没有最小重试机制，会让 CI 可信度下降

这时候真正需要补的不是更多 eval，而是 suite 的执行策略。

## 任务目标

- 让 suite 支持根据变更文件选择受影响能力线
- 让 step 支持最小失败重试
- 让 PR 能更快得到反馈，同时不放弃主分支全量回归

## 交付标准

- 至少支持通过 changed files 推断 active scopes
- 至少支持 step 级重试与 attempts 指标
- 至少能在 CI 中区分 `changed-scoped` 和 `full` 两种运行模式
