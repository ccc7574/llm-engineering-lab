# H26: 给 Harness 补 latency / cost trend board

## 背景

当前 Harness 已经能回答:

- 回归有没有过
- 哪条能力线 regressed / flat / passed
- 当前 cost signal 有哪些变化

但真实团队还需要继续回答:

- 这次 suite 比上一次更慢了吗
- 哪几个 step 正在成为新的耗时热点
- 哪条能力线的 cost drift 正在持续放大

## 任务目标

- 从 `summary_board` 和 `regression_suite_report` 生成 trend snapshot
- 支持把当前 snapshot 与上一版 snapshot 做对比
- 输出适合 reviewer / release owner 阅读的 latency / cost trend board

## 交付标准

- 至少能展示当前 suite 总耗时和最慢 step
- 至少能展示各 track 的 cost signal 概览
- 至少在提供 baseline snapshot 时输出 step duration drift 和 cost drift
