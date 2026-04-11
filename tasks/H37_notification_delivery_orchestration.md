# H37: 把 routing、dispatch policy 和 live dispatch 串成统一 delivery 入口

## 背景

当通知链已经有:

- digest
- route
- dispatch policy
- dispatch result

团队仍然会遇到一个很实际的问题:

- 本地要手工串多个命令
- workflow 里要重复拼 route / policy / dispatch 逻辑
- reviewer 很难快速判断“这次到底尝试没尝试发、为什么没发、发到了哪”

这时缺的不是再加一个零散脚本，而是把 delivery 过程收敛成一个统一 orchestration 入口。

## 任务目标

- 新增统一 notification delivery 脚本
- 让它负责 route、dispatch policy 和 dispatch 编排
- 同时落盘 route / policy / dispatch / delivery 四类 artifact

## 交付标准

- 至少支持 `event / default channel / override channel` 三类输入
- 至少能输出 `notification_delivery.json` 和 `notification_delivery.md`
- 至少能在 policy deny、缺失 payload、dry-run、真实 dispatch 四种路径下产出结构化结果
- 至少让 workflow 改为复用统一 delivery 入口，而不是手工拼多段逻辑
