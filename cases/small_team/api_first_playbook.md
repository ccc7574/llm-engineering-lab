# Small Team Playbook: API First 快速交付

## 适用场景

你在一个 3-10 人的小团队，需要用最少的人力和算力，把 AI 能力尽快接进真实产品。重点不是“做自己的基础模型”，而是用最小训练和最强 harness 把价值验证出来。

## 团队画像

- 角色: 全栈工程师、产品工程师、创始人/负责人
- 资源: 基本依赖 API，少量微调预算
- 压力: 时间紧、成本敏感、容错空间小

## 优先能力线

1. `Harness`
2. `Post-Training`
3. `Agentic`
4. `Coding`

## 推荐任务组合

- `S00-S11`
- `A00-A10`
- `H00-H18`
- `C00-C03`

## 30/60/90 天路线

### 30 天

- 跑通最小 SFT / structured output / eval
- 用 harness 建立发布前检查和成本意识
- 用 agentic workflow 验证真实业务流程

### 60 天

- 补 retry、idempotency、review summary、route policy
- 把 coding / testgen 接进真实研发流程
- 做 1-2 个真正能省人工的自动化场景

### 90 天

- 明确哪些能力继续保留自有资产，哪些完全依赖第三方 API
- 建立最小发布说明、值班和回归节奏

## 必须建立的工程能力

- 小而稳的 eval 与 release gate
- 低成本 dispatch 和通知治理
- prompt / workflow / agentic 的快速回归

## 不应该先做的事

- 没有用户价值前就投入重型训练
- 盲目追逐复杂多模态和多代理架构
- 用“demo 看起来不错”替代回归和发布标准

