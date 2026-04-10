# P03: 拆解 Transformer Block

## 背景

非算法工程师不需要从零手写完整论文实现，但必须知道一个 block 里有哪些关键组件，以及这些组件各自改变了什么。

## 任务目标

- 读懂 embedding、attention、MLP、residual、layer norm 的连接关系
- 能把 block 结构和训练行为对应起来
- 建立后续讨论 context length、stability、continued pretraining 的基础

## 业务与资源约束

- 优先读最小代码，不引入大框架
- 重点是结构理解，不是速度优化

## 代码改造点

- `code/stage1_nanogpt_core/model.py`
- `code/stage1_nanogpt_core/train.py`

## 交付标准

- 能画出最小 block 数据流
- 能解释 residual 和 layer norm 为什么重要
- 能指出 attention 和 MLP 分别解决什么问题

## 原理补充

这一单的重点不是背公式，而是建立“一个 block 为什么足以表达复杂条件生成”的工程直觉。

## 实验步骤

1. 阅读 `model.py` 的 block 定义
2. 对照训练日志和采样行为理解各层作用
3. 输出一份 block 结构说明

## 结果解读

能把代码结构讲清，才算真正进入后续训练优化讨论。

## 线上风险

- 只背概念，不映射到代码
- 把 block 结构当成黑盒，后续排障困难

## 复盘与延伸

- 对应旧任务: `T03`
- 下一步进入 `P10-P12`

