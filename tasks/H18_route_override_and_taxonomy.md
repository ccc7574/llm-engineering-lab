# H18: 给通知链补 route override 和更细的 failure taxonomy

## 背景

当通知系统已经具备 route policy 之后，团队还会遇到两个现实问题:

- 某次手工触发需要临时强制走某个通道
- 失败原因太粗，无法支持后续更细粒度的通知决策

这意味着通知链不仅要“自动”，还要“可覆盖”和“可解释”。

## 任务目标

- 支持 route override
- 细化 suite failure taxonomy
- 把更细的 failure counts 暴露给 route / digest 层

## 交付标准

- 至少支持一条显式 override channel 参数
- 至少新增多类 runtime failure taxonomy
- 至少让 route artifact 带上 override 和 failure counts 信息
