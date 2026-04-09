# T30: 做一个最小 DPO 实验，理解偏好优化如何改变输出

## 背景

团队已经有了基础助手，也有了最小推理增强。现在的问题变成: “为什么有些回答虽然不算错，但就是不够像我们想要的样子?” 这时就可以引入最小偏好优化实验。

## 任务目标

- 组织 chosen / rejected 对
- 训练一个 toy DPO 模型
- 观察模型输出风格和选择倾向的变化

## 业务约束

- 明确这是教学级最小实验
- 不追求大规模效果
- 必须能解释 reference model 的作用

## 你需要改的代码

- `datasets/tiny_preferences/train.jsonl`
- `code/stage5_toy_alignment/train_dpo.py`

## 交付标准

- 跑通一轮 DPO 损失
- 给出偏好前后样例对照
- 解释偏好优化和 SFT 的差异

