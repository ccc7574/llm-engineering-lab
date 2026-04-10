# Bigtech Playbook: 模型平台升级与发布治理

## 适用场景

你在一家一线 AI 大公司，负责把通用模型能力稳定交付给多个内部产品线。你的工作重点不是“先做出一个能跑的 demo”，而是让训练、评测、发布和回滚都具备平台化标准。

## 团队画像

- 角色: pretraining engineer、post-training engineer、eval engineer、release owner、platform engineer
- 资源: 有集群、有标注预算、有较成熟数据平台
- 压力: 多团队复用、线上风险高、回归和治理要求严

## 优先能力线

1. `Harness`
2. `Pretraining`
3. `Post-Training`
4. `Coding`

## 推荐任务组合

- `P10-P20`
- `S10-S22`
- `C10-C20`
- `H10-H32`

## 30/60/90 天路线

### 30 天

- 跑通统一 regression suite
- 明确发布 gate 和 failure taxonomy
- 补齐 route policy / review summary / release note

### 60 天

- 做 continued pretraining 与数据 mixture 对照
- 引入 reasoning / verifier / rejection sampling 路线比较
- 建立 golden artifact 和 baseline 版本化

### 90 天

- 把 policy review、发布说明、PR comment、trend board 全接进平台流程
- 对多条模型路线形成统一评测与回滚标准

## 必须建立的工程能力

- manifest-driven eval
- baseline vs candidate regression
- route diff / policy gate
- provider-aware dispatch 和发布可观测性

## 不应该先做的事

- 在没有稳定 eval 的情况下大规模调参
- 把所有收益都归因于模型结构
- 忽视回滚与发布治理

