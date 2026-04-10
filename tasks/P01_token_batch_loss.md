# P01: 看懂 token、batch 和 loss

## 背景

很多工程师会运行训练脚本，但并不真正理解 token 是怎么组成 batch、loss 为什么会波动，以及这些信号为什么决定训练是否可信。

## 任务目标

- 看懂 tokenization、batch slicing 和 target shift
- 解释 batch 构造为什么会影响梯度噪声
- 用最小实验观察 loss 的下降与抖动

## 业务与资源约束

- 不引入复杂数据管线
- 只在 tiny 数据集上观察机制

## 代码改造点

- `code/stage1_nanogpt_core/debug_batch.py`
- `code/stage1_nanogpt_core/train.py`

## 交付标准

- 能打印并解释一个 batch 的输入与目标
- 能说清交叉熵 loss 在这个项目里的含义
- 能说明 batch size 改变后 loss 曲线会怎么变

## 原理补充

这一单要建立训练可解释性: token 是最小学习单位，batch 是梯度统计窗口，loss 是当前分布拟合程度的近似指标。

## 实验步骤

1. 用 `debug_batch.py` 检查 token 和 target
2. 用不同 batch size 训练短跑
3. 比较 loss 曲线和样本输出

## 结果解读

如果 loss 下降但样本没有改善，通常说明训练太短或指标粒度不够；如果 loss 完全不动，优先检查 token 与 target 对齐。

## 线上风险

- label shift 配错会让模型学不到有效映射
- 只看单点 loss，忽视 batch 方差

## 复盘与延伸

- 对应旧任务: `T01`
- 下一步进入 `P02`

