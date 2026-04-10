# S21: 做一个最小 GRPO / Reward-Guided Update 实验

## 背景

当团队希望把“更偏好哪种回答”转成训练信号时，下一层就会接触 reward-guided update。对教学仓库来说，最合适的是保留一个可解释的 toy 版本。

## 任务目标

- 定义最小 reward 或相对优劣信号
- 跑通一轮 toy policy update
- 理解 GRPO 类方法与 DPO 的差别

## 业务与资源约束

- 必须可解释
- 必须保留失败成本视角

## 代码改造点

- `code/stage5_toy_alignment/train_grpo.py`
- `datasets/tiny_preferences/`

## 交付标准

- 至少跑通一轮最小更新
- 至少输出 reward / preference 相关日志
- 能解释为什么这类方法更难调

## 原理补充

reward-guided update 更接近“用偏好或奖励驱动策略变化”，但稳定性、奖励设计和成本都更敏感。

## 实验步骤

1. 设计最小 reward 信号
2. 跑一轮 toy update
3. 对比更新前后样例

## 结果解读

重点看训练是否稳定、奖励是否和想要的行为一致。

## 线上风险

- 奖励黑客
- 更新不稳定

## 复盘与延伸

- 对应旧任务: `T31`
- 当前仓库下一步要补 runnable code

