# H15: 给 regression digest 生成外部通知 payload

## 背景

有了 digest 之后，团队离真正的通知外发只差一步:

- 让摘要变成各平台可直接发送的 payload

如果每个接入方都从头拼消息，很快就会出现格式漂移和字段不一致。

## 任务目标

- 基于统一 digest 生成 Slack / 飞书 payload
- 让外部通知层和 suite / gate 层解耦
- 为后续 webhook、机器人或 IM skill 接入留出稳定接口

## 交付标准

- 至少输出一种英文协作平台 payload
- 至少输出一种中文协作平台 payload
- 至少保留 headline、severity、gate、failed steps 这些核心字段
