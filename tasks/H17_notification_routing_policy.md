# H17: 给通知链补上 routing policy

## 背景

当通知链已经具备:

- digest
- payload
- dispatch

下一步真正影响团队运行方式的问题就变成了:

- 哪些事件该发
- 发到哪个通道
- 什么情况下不发

这些规则如果直接写死在 workflow 里，很快会变得难维护。

## 任务目标

- 把通知路由规则抽成 manifest
- 基于 event / severity / ship_ready 选择 channel
- 让 workflow 和 dispatch 只消费 route 结果，不再直接硬编码路由逻辑

## 交付标准

- 至少有一份可机读 routing policy
- 至少能输出 route artifact
- 至少支持按 event 和 severity 选择 channel
