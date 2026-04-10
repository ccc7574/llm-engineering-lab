# H28: 给 Harness 补 PR Comment / Release Note 自动生成

## 背景

当前 Harness 已经有:

- notification digest
- review summary
- trend board
- suite report
- summary board

但 reviewer 和 release owner 仍然需要自己从多份 artifact 里拼出“这次能不能发、为什么、风险在哪”。

## 任务目标

- 生成统一的 PR comment / release note artifact
- 把 release gate、policy gate、dispatch 状态、track 状态和 trend 信号压到一张卡片
- 让 GitHub Job Summary 和后续 PR comment / release bot 直接复用同一份内容

## 交付标准

- 至少输出 JSON 和 Markdown 两种 artifact
- 至少总结 reviewer checklist、track statuses、slowest steps 和 cost drift
- 至少能在 workflow 中自动产出
