# H16: 把 notification payload 推进到可发送的 dispatch 层

## 背景

payload artifact 解决了“消息长什么样”，但还没有解决“谁来发、怎么发、没配置时怎么办”。

真实团队通常还会补一层 dispatch:

- 本地可以 dry-run
- CI 可以按 secret 决定是否真的发送
- 不同通道共用同一份 payload 资产

## 任务目标

- 新增统一 notification dispatch 脚本
- 支持 stdout、webhook 和 dry-run
- 让外发逻辑与 payload 生成逻辑解耦

## 交付标准

- 至少支持一种 dry-run 模式
- 至少支持从环境变量读取 webhook
- 至少支持基于现有 payload artifact 发送
