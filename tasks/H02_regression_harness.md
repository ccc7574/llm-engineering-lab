# H02: 做一套 regression harness，让每次改动都能被量化验证

## 背景

没有 regression harness 的团队，模型迭代很容易退化成“靠感觉判断”。今天看起来好了，明天发现结构化输出坏了，后天发现 latency 爆了，谁都说不清是哪次改动造成的。

## 任务目标

- 为关键任务建立回归评测入口
- 把能力、格式、稳定性和成本一起纳入判断
- 让每次改动后都能快速知道是否值得保留

## 业务与资源约束

- 评测必须足够快，不能拖垮迭代速度
- 指标必须足够直观，便于团队讨论
- 先覆盖最关键任务，不追求全量 benchmark

## 代码改造点

- `eval/`
- `datasets/`
- `runs/`
- `code/stage_harness/regression_compare.py`
- `code/stage_harness/summary_board.py`

## 交付标准

- 至少支持一组固定回归任务
- 至少输出能力指标和工程指标
- 至少能对比 baseline 与 candidate run
- 至少输出一个团队可读的统一汇总视图

## 原理补充

regression harness 的核心价值是:

1. 把实验结果变成团队共识
2. 把“改进”定义得更具体
3. 避免局部优化破坏整体表现

## 实验步骤

1. 选定核心回归任务
2. 定义 baseline checkpoint
3. 跑 candidate checkpoint
4. 输出对照报告

## 结果解读

读者应该知道:

- eval 不是项目尾声才需要的东西
- regression harness 是日常工程节奏的一部分

## 线上风险

- 回归集太小，无法代表真实变化
- 指标过多，团队无法快速判断
- 只看能力，不看 latency 与 cost

## 复盘与延伸

下一步自然进入:

- `H03` latency / cost profiling
- `H10` 发布与回滚标准
