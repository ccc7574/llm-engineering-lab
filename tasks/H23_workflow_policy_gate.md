# H23: 把通知策略 gate 接进 workflow

## 背景

本地已经有:

- route lint
- route matrix
- route diff
- policy gate

如果这些检查不进入 workflow，它们对团队协作的约束力仍然有限。

## 任务目标

- 把通知策略检查接进 GitHub Actions workflow
- 让 workflow 默认产出 route review artifact
- 让通知策略 gate 可以像主 suite gate 一样被 CI 执行

## 交付标准

- 至少在 workflow 中生成 baseline / candidate route matrix
- 至少在 workflow 中生成 route diff 和 policy gate report
- 至少支持开关式 `require_policy_gate`
