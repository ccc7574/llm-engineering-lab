# H14: 给 regression suite 增加 notification digest

## 背景

当回归结果开始包含:

- suite status
- gate 决策
- 失败步骤
- regression rows

原始 JSON 虽然完整，但已经不适合直接发给值班同学或发布负责人。

团队通常还需要一层更短、更可读的通知摘要。

## 任务目标

- 基于 suite report、summary board、gate report 生成统一 digest
- 对失败原因做最小 taxonomy 分类
- 输出既适合机器读取也适合人阅读的通知 artifact

## 交付标准

- 至少输出 digest JSON
- 至少输出 digest Markdown
- 至少包含 severity、headline、failed steps、gate 结论
