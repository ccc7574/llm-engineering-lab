# H31: 给通知策略补 failure-category-aware routing

## 背景

当 notification chain 已经支持:

- failure taxonomy
- notification digest
- routing policy
- route matrix / diff / lint / gate

下一步就不该只按 `event / severity / gate` 做粗粒度路由。

真实团队里经常会遇到:

- 同样是 `warning`，但权限问题需要立刻打到更高优先级通道
- report 解析失败不一定代表业务失败，但需要更快暴露给平台或基础设施 owner
- policy review 不能只看最终 channel，还要看是哪一类 failure 触发了分流

## 任务目标

- 让 route rule 可以直接按 `failure_categories` 匹配
- 让 route matrix / diff / gate / lint 都显式覆盖 failure category 维度
- 让 digest 与 route artifact 带上 `top_failure_category` 和命中分类信息

## 交付标准

- 至少支持在 `notification_routes.json` 中声明 `failure_categories`
- 至少让 route matrix / diff 行键包含 `failure_category`
- 至少让 policy gate 能对 failure-category-aware 行为变化做 allowlist 守门
