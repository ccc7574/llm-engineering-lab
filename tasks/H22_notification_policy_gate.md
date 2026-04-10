# H22: 给通知策略补 lint 和 regression gate

## 背景

当通知策略已经有:

- route manifest
- route matrix
- route diff

下一步就不应该只停留在“能看见变化”，而应该进入“能自动守住边界”。

## 任务目标

- 对 route manifest 做最小 lint
- 对 route diff 做 gate 判断
- 让通知策略也能像模型回归一样进入 CI 守门流程

## 交付标准

- 至少能检查未知 channel 和重复 selector
- 至少能对 route diff 做 `ship / hold` 判断
- 至少能配置允许的 changed rows 范围
