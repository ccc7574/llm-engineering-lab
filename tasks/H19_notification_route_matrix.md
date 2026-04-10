# H19: 给通知路由策略生成 route matrix

## 背景

当 routing policy 变得越来越复杂之后，单独跑一个 case 已经不够了。

团队还需要一种更直观的方式，去回答:

- 不同事件下会发到哪
- 不同严重度下会发到哪
- 改了路由规则之后，整体矩阵是否仍符合预期

## 任务目标

- 生成 notification route matrix
- 让 route policy 的行为变成可审阅 artifact
- 为后续 policy review 提供最小回归视图

## 交付标准

- 至少输出 route matrix JSON
- 至少输出 route matrix Markdown
- 至少覆盖 event、severity、gate 三个维度
