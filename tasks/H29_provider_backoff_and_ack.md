# H29: 给通知 dispatch 补 provider-aware backoff 和 ack

## 背景

当 dispatch 已经支持:

- retry
- idempotency
- result artifact

下一步就不能再把所有 webhook 都当成同一种 provider。

真实团队里至少要区分:

- Slack 的 `200 + ok`
- 飞书的 JSON ack
- rate limit / transient / permanent rejection 三类失败

## 任务目标

- 给不同 channel 增加 provider-aware ack 解析
- 让 retry 只发生在真正可重试的场景
- 让 dispatch result 带上 `ack_status`、`failure_category`、`provider` 等字段

## 交付标准

- 至少区分 Slack 和飞书两类 ack 规则
- 至少区分 `success / rate_limit / provider_error / permanent_rejection / network_error`
- 至少让 attempts 记录里包含 retryable 和 next delay 信息
