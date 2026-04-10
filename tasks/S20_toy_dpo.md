# S20: 做一个最小 DPO 实验

## 背景

当团队已经有 SFT 和最小 reasoning 路线后，下一层常见问题是“回答不算错，但不够符合我们偏好”。这时可以引入最小 DPO。

参考图:

- [post_training_alignment_loop.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/post_training_alignment_loop.svg)

## 任务目标

- 组织 chosen / rejected 偏好对
- 训练最小 DPO 路线
- 观察偏好优化对输出风格和选择倾向的影响

## 业务与资源约束

- 明确这是教学级 toy 实验
- 不追求大规模效果

## 代码改造点

- `datasets/tiny_preferences/train.jsonl`
- `code/stage5_toy_alignment/train_dpo.py`

## 交付标准

- 跑通最小 DPO 损失
- 给出偏好前后样例
- 能解释 DPO 与 SFT 的差异

## 原理补充

DPO 的核心不是“让模型更聪明”，而是让模型在已有能力上更倾向 chosen 风格。

## 实验步骤

1. 准备偏好对
2. 跑 toy DPO
3. 对比样例输出

## 结果解读

重点看风格偏移和拒答/表达倾向变化，而不只是单纯正确率。

## 线上风险

- 偏好数据噪声高
- reference model 管理混乱

## 复盘与延伸

- 对应旧任务: `T30`
- 当前仓库下一步要补 runnable code
