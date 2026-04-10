# H33: 给 live notification adapter 补安全边界

## 背景

当 dispatch 已经支持:

- retry
- idempotency
- provider-aware ack
- route / dispatch policy

下一步不能再把 live webhook 发送视为“只要 URL 在就发”。

真实团队里至少还需要:

- provider host allowlist，防止 secret 或 payload 被发到错误地址
- provider-specific signing，避免外发链路完全依赖 URL 保密
- 安全诊断字段，让值班同学知道这次 dispatch 用了什么 secret / signature 模式

## 任务目标

- 对 live webhook 做 scheme / host 校验
- 给 Feishu custom bot 增加 secret signing 支持
- 把安全上下文写进 dispatch result artifact

## 交付标准

- 至少拒绝非 `https` 和非 provider allowlist host
- 至少支持 `FEISHU_WEBHOOK_SECRET` 或 `--signing-secret`
- 至少在 `notification_dispatch_result.json` 里输出 `security` 诊断字段
