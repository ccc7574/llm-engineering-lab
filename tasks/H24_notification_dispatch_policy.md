# H24: 给通知链补真实 dispatch policy

## 背景

当 routing policy 已经能回答“应该路由到哪里”，团队还缺一层更现实的约束:

- 这个 run 是不是允许真实外发
- schedule、manual、PR 是否应该走同一套 live dispatch 规则
- override 是不是应该被视为一种显式值班操作

## 任务目标

- 给通知链增加 dispatch allow/deny 决策层
- 让 workflow 能区分“artifact 已生成”和“允许真实发送”
- 默认避免 PR / push 等高频事件造成通知噪音

## 交付标准

- 至少能按 `event / severity / gate / channel / override` 做 dispatch 决策
- 至少能输出 `allow_dispatch` 和明确 `reason`
- 至少能让 workflow 只在 policy 允许时执行真实 dispatch
