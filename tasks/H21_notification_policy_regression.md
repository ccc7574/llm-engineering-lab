# H21: 给通知策略补 regression diff

## 背景

通知策略一旦开始演化，就不应该只靠人眼看 manifest 变化。

团队还需要知道:

- 哪些 event/severity/gate 组合的路由变了
- 是不是只有预期中的几行变了
- policy 调整有没有带来意外扩散

## 任务目标

- 让 notification policy 也具备 baseline vs candidate diff
- 输出 route diff JSON 和 Markdown
- 让通知规则的变更也能进入 review 和回归流程

## 交付标准

- 至少支持两份 route matrix 的对比
- 至少输出 changed rows 数量
- 至少输出按 event / severity / gate 展示的 diff
