# P00: 跑通最小预训练闭环

## 背景

你接手的不是已经会对话的助手，而是一套只能做 next-token prediction 的最小语言模型。要让非算法工程师真正理解后续所有优化从哪里开始，第一步必须先把最小预训练链路跑通。

## 任务目标

- 用极小语料跑通一次最小训练
- 产出训练前后生成结果
- 建立统一 checkpoint 与运行入口

## 业务与资源约束

- 默认单机 CPU 或单卡可跑
- 30 分钟内应能完成一次 smoke run
- 不追求效果，只追求闭环完整

## 代码改造点

- `code/stage0_bigram/train_bigram.py`
- `code/stage0_bigram/sample_bigram.py`
- `datasets/tiny_shakespeare/input.txt`

## 交付标准

- 能成功训练并保存 checkpoint
- 能从 checkpoint 采样
- 能解释训练前后输出为何不同

## 原理补充

这一单只讲清一件事: 预训练的本质是根据前文预测下一个 token。如果这条链路没有操作感，后面谈 context、SFT、alignment 都会失焦。

## 实验步骤

1. 运行 `train_bigram.py`
2. 用 `sample_bigram.py` 采样
3. 记录 loss 和样本文本

## 结果解读

重点看 loss 是否下降、输出是否从噪声变成“有局部结构的文本”。

## 线上风险

- 入口混乱导致新同学不知道从哪里开始
- checkpoint 路径不统一导致复现失败

## 复盘与延伸

- 对应旧任务: `T00`
- 下一步进入 `P01` 和 `P02`

