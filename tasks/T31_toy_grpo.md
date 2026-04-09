# T31: 做一个 Toy GRPO 风格实验，理解基于奖励的更新

## 背景

如果说 DPO 更像离线偏好比较，那么 GRPO 风格方法更像“让模型自己生成一组候选，再按照组内相对奖励来更新”。这能帮助工程师理解为什么 online sampling 会带来额外复杂度和额外灵活性。

## 任务目标

- 为同一 prompt 生成一组候选
- 计算组内相对奖励
- 让策略在正确答案方向上更偏好高奖励样本

## 业务约束

- 只做 toy 级别，不做复杂 PPO 工程
- 奖励函数必须简单、透明
- 明确展示组内归一化的作用

## 你需要改的代码

- `code/stage5_toy_alignment/train_grpo.py`
- `datasets/tiny_reasoning/train.jsonl`

## 交付标准

- 能生成 group samples
- 能计算 group-relative advantage
- 能输出训练前后的样例对照

