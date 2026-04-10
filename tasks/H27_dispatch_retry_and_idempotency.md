# H27: 给通知 dispatch 补 retry 和 idempotency

## 背景

当通知链已经允许真实外发后，dispatch 入口就不应该只是一次性 webhook 调用。

真实团队里至少会遇到:

- webhook 临时网络抖动
- workflow retry 或手工重复触发
- 同一条通知被重复发送到值班通道

## 任务目标

- 给 dispatch 增加最小重试能力
- 给 dispatch 增加幂等键和重复发送抑制
- 让 dispatch 产出结构化结果报告，便于 CI artifact 和值班复盘

## 交付标准

- 至少支持 `max-attempts` 和 `retry-delay-seconds`
- 至少支持 idempotency key、状态文件和重复发送跳过
- 至少输出 `notification_dispatch_result.json` 一类结果 artifact
