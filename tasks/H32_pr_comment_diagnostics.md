# H32: 给 PR comment 回写补权限诊断与可观测性

## 背景

当 PR comment writeback 已经支持:

- marker-based upsert
- create / update
- allow-failure / missing-token fallback

下一步不能只在失败时吐出一段原始 GitHub API 响应。

真实团队里最常见的问题不是“脚本不会写评论”，而是:

- fork 场景 token 无法写回
- workflow 权限没开全
- repo / PR 编号或访问上下文不对
- reviewer 只能看到 `403` 或 `404`，不知道下一步该改什么

## 任务目标

- 给 PR comment result 增加结构化 diagnosis 和 actionable hint
- 区分 missing token、invalid token、insufficient permission、repo/PR not found 等失败类别
- 把 writeback 结果同步进 markdown artifact 和 workflow summary

## 交付标准

- 至少支持 `403 / 404 / 422` 的分类诊断
- 至少输出 JSON 和 Markdown 两种 PR comment result artifact
- 至少让 workflow summary 能直接看到 writeback 结果和下一步处理建议
