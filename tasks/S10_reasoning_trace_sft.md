# S10: 做 Reasoning Trace SFT

## 背景

很多团队会把“模型推理更强了”归因于模型本身，但在小规模实验里，更常见的变化来自 reasoning trace 数据。

## 任务目标

- 把 reasoning trace 样本并入 SFT 路线
- 比较普通回答和带 trace 的回答差异
- 理解 trace 对行为和成本的影响

## 业务与资源约束

- 数据规模小，但格式必须一致
- 必须同时看收益和输出长度成本

## 代码改造点

- `code/stage2_sft/train_sft.py`
- `datasets/tiny_reasoning/`
- `eval/reasoning_eval.py`

## 交付标准

- 能把 reasoning 数据接进训练
- 能对比 trace 前后正确率和输出长度
- 能解释 trace 为什么有时有效、有时只是冗长

## 原理补充

trace SFT 常常改变的是“推理风格”和“中间步骤显式化”，不等于真正提升了底层能力上限。

## 实验步骤

1. 训练普通 SFT 和 trace SFT
2. 跑 reasoning eval
3. 对比正确率和长度

## 结果解读

重点看 trace 是否真的提高了正确候选覆盖率，而不是只让回答更长。

## 线上风险

- 长回答带来成本上升
- 形成过度解释风格

## 复盘与延伸

- 对应旧任务: `T22`
- 下一步进入 `S11`

