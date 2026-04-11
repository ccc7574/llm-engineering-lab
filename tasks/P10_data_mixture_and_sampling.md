# P10: 设计数据混合与采样策略

## 背景

真实模型团队做预训练优化时，首先改的通常不是网络结构，而是数据分布。对工程师来说，理解 mixture 和 sampling 比理解更多 trick 更重要。

参考图:

- [pretraining_data_mixture_map.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/pretraining_data_mixture_map.svg)

## 任务目标

- 设计最小多源数据混合方案
- 比较均匀采样和偏置采样的影响
- 学会用失败样本反推数据问题

## 业务与资源约束

- 只能使用 tiny 级数据
- 不追求大规模收益，只追求机制可见

## 代码改造点

- `datasets/`
- `code/stage1_nanogpt_core/train_mixture.py`
- 可新增最小 mixture manifest

## 交付标准

- 定义至少两种采样策略
- 给出不同 mixture 下的输出差异
- 解释为什么数据分布会塑造能力边界

## 原理补充

预训练阶段最现实的杠杆常常是“喂什么数据、按什么比例喂、在哪些阶段加权”，而不是盲目加参数。

## 实验步骤

1. 准备 `uniform` 和 `domain-heavy` 两种 mixture manifest
2. 用 `train_mixture.py` 跑短训练
3. 比较 per-source loss 和输出偏移

## 结果解读

重点看能力是否向目标领域偏移，以及是否出现泛化退化。

## 线上风险

- 垂直数据过采样导致遗忘
- 数据污染让结论失真

## 复盘与延伸

- 对应 roadmap: `P10`
- 下一步进入 `P11`
