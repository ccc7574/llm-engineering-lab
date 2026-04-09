# H01: 建立 checkpoint 与 config registry，避免实验资产失控

## 背景

一旦训练实验开始增多，团队很快就会遇到这些问题:

- 这个 checkpoint 是哪次训练出来的
- 当时用的参数是什么
- 为什么这版看起来更好却复现不出来
- 哪个结果可以拿去做基线

如果没有 registry，实验资产会迅速失控。

## 任务目标

- 建立 checkpoint 和 config 的最小登记规范
- 让训练结果、参数、指标之间能追溯
- 给后续回归和发布提供基础记录

## 业务与资源约束

- 先求可追踪，不求复杂平台
- 先支持本地文件和 JSON 记录
- 要兼容已有 `runs/` 结构

## 代码改造点

- `runs/`
- `docs/runbook.md`
- `code/common/`
- 可新增 `registry` 相关文件

## 交付标准

- 至少记录 checkpoint、config、关键指标、时间
- 至少支持通过一个记录文件回溯一次训练
- 至少区分 smoke run、baseline run、candidate run

## 原理补充

registry 的价值在于:

1. 让实验结果可审计
2. 让对照实验真正可比
3. 让团队知道“哪一个模型值得继续用”

## 实验步骤

1. 扫描现有 `runs/`
2. 定义最小 metadata schema
3. 给已有运行结果补登记信息
4. 检查是否能回溯关键实验

## 结果解读

读者应该知道:

- 训练资产管理是模型工程能力，不是杂事
- 没有 registry，团队很难形成持续迭代能力

## 线上风险

- checkpoint 和指标脱钩
- baseline 被误删或误用
- 配置漂移导致结果不可比

## 复盘与延伸

完成后可进入:

- `H02` regression harness
- `H10` 发布与回滚标准
