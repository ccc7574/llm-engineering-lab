# H25: 给 reviewer 补压缩通知审阅摘要

## 背景

通知链现在已经能产出:

- digest
- route
- route diff
- policy gate
- dispatch policy

但 reviewer 仍然需要跨多个 artifact 才能快速判断“这次 CI 到底有没有风险、会不会发通知、是否需要介入”。

## 任务目标

- 生成面向 reviewer / release owner 的压缩 summary
- 把 release gate、route gate、dispatch gate 放到同一张卡片里
- 让 GitHub Job Summary 顶部直接出现可行动结论

## 交付标准

- 至少同时总结 suite gate、route gate 和 dispatch gate
- 至少列出 failed steps / failure counts / active scopes 中的关键信息
- 至少能输出 JSON 和 Markdown 两种 artifact
