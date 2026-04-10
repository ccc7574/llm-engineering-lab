# H30: 给 Harness 补真正的 PR comment 回写

## 背景

当 release note 已经能自动生成之后，下一步就不该只停留在 artifact 和 Job Summary。

真实团队里 reviewer 通常会直接在 PR 页面上看:

- 当前是否 ready / hold / block
- 哪些能力线需要关注
- 最近的 trend / dispatch / gate 状态

## 任务目标

- 把 release note 自动写回 PR comment
- 使用 marker 复用同一条评论，避免每次 workflow 都刷屏
- 让 fork / 缺 token / 权限不足时能优雅降级，而不是把整条回归链拖挂

## 交付标准

- 至少支持 create / update 两种模式
- 至少支持 marker-based upsert
- 至少能输出结构化 PR comment result artifact
