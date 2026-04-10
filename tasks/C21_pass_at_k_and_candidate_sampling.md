# C21: 把 coding 评测从单候选推进到 pass@k 与 test-time sampling

## 背景

真实代码模型评测很少只看一发命中。

更常见的问题是:

- greedy 第一发经常不够好
- 采样后候选里其实已经出现可通过实现
- 团队需要知道“多采几次值不值”

这就是 `pass@k` 的工程意义。

## 任务目标

- 建立最小 `single_sample -> sample_k` 对照
- 让读者看到多候选采样如何改变 execution-based 通过率
- 把 `pass@1`、`pass@k` 和额外执行成本一起放进同一个评测视图

## 交付标准

- 至少有一组带多候选样本的 coding 任务
- 至少输出 `pass_at_1` 与 `pass_at_k`
- 至少记录 `avg_candidates_sampled`、`avg_execution_checks`、`avg_first_pass_index`
- 至少把该路径接入 regression suite
