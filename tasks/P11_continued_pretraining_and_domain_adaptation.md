# P11: 做 Continued Pretraining / Domain Adaptation

## 背景

对中型和小型 AI 团队来说，真正可落地的预训练路线往往不是从零训，而是在现有 base model 上做 continued pretraining。

## 任务目标

- 用小规模领域数据做 domain adaptation
- 比较 adaptation 前后的领域表现
- 理解 continued pretraining 与 SFT 的边界

## 业务与资源约束

- 只能在已有 checkpoint 基础上微调
- 算力预算有限

## 代码改造点

- `code/stage1_nanogpt_core/continue_pretraining.py`
- `runs/stage1_gpt/ckpt.pt`
- 新增或扩展领域数据集

## 交付标准

- 能从已有 checkpoint 继续训练
- 能对比通用样本与领域样本表现
- 能解释什么时候该做 continued pretraining，什么时候该做 SFT

## 原理补充

continued pretraining 改的是底层分布适应，SFT 改的是交互协议和行为风格，两者不能混为一谈。

## 实验步骤

1. 准备领域数据和通用 eval set
2. 从已有 checkpoint 继续训练
3. 比较 adaptation 前后的 domain/general loss

## 结果解读

如果领域样本显著改善而通用样本保持可接受，说明 adaptation 有价值；如果通用能力明显下滑，要警惕灾难性遗忘。

## 线上风险

- 领域语料过窄导致过拟合
- checkpoint 管理不规范导致回滚困难

## 复盘与延伸

- 对应 roadmap: `P11`
- 下一步进入 `P12` 和 `P20`
