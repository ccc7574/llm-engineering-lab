# H36: 让 Harness 能从 suite report 直接生成 failure replay plan

## 背景

CI 失败后，团队最常见的下一句不是“为什么失败”，而是“我现在应该重放哪一步”。

如果 suite report 只能告诉你失败了，却不能给出 replay command，值班和 reviewer 还是要手工拼命令。

## 任务目标

- 从 suite report 中提取失败步骤
- 直接输出 replay command
- 从 eval report 中继续拆出 task / sample 级 replay command
- 把失败分类、缺失产物和失败样本一起放进重放计划

## 交付标准

- 至少输出 `json + md` 两种 replay plan
- 至少包含失败 step、failure category、replay command
- 至少能识别 `passed / success / pass_at_k_hit / useful` 四类失败信号
- task / sample replay 需要自动改写成独立 `--task-id ... --report-path runs/replay/...`
- 在 suite 全绿时也能优雅输出“当前无失败步骤”
