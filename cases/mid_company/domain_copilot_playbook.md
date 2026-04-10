# Mid Company Playbook: 垂直 Copilot 能力强化

## 适用场景

你在一家中型 AI 公司，目标是在 1-2 个高价值业务场景里把模型能力做深，而不是覆盖所有通用能力。团队有有限训练资源，但必须对质量、成本和业务转化负责。

## 团队画像

- 角色: 应用工程师、MLE、平台工程师、产品经理
- 资源: 有一定微调能力，有垂直数据，但算力预算有限
- 压力: 需要尽快证明 ROI，同时不能把系统做得太重

## 优先能力线

1. `Post-Training`
2. `Coding`
3. `Agentic`
4. `Harness`

## 推荐任务组合

- `S00-S12`
- `C00-C13`
- `A00-A10`
- `H00-H25`

## 30/60/90 天路线

### 30 天

- 先把 SFT、structured output、最小 eval pack 做稳
- 用 harness 建立统一基线
- 找到最赚钱或最省人工的垂直任务

### 60 天

- 补 reasoning / verifier / rejection sampling
- 引入 agentic workflow 和 coding 任务对照
- 把 latency / cost / dispatch 进入日常评审

### 90 天

- 针对垂直流程沉淀 release note、review summary、持续回归
- 明确哪些能力值得继续自训，哪些改成 API 或 workflow 补强

## 必须建立的工程能力

- 面向业务的 eval pack
- 质量/成本联动观察
- 小步快跑的 regression suite
- 结构化发布与值班摘要

## 不应该先做的事

- 在没有业务指标前盲目做重型预训练
- 把多代理系统堆到过度复杂
- 忽视 harness，导致每次优化都无法解释

