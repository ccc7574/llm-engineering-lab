# H34: 给 Harness 增加 artifact catalog 和生命周期治理

## 背景

当 suite、summary、gate、route、release note 都开始生成时，团队很快会遇到新问题:

- 哪些 artifact 只是调试临时产物
- 哪些 artifact 应该跟发布一起保留
- 哪些 artifact 应该被纳入基线快照

如果没有 artifact catalog，产物再多也只是“目录越来越乱”。

## 任务目标

- 建立最小 artifact catalog
- 给每类 artifact 打上生命周期标签
- 让团队能区分 `promote_on_ship`、`retain_for_replay` 和 `ephemeral_debug`

## 交付标准

- 至少能扫描 `runs/` 下当前 artifact
- 至少输出 `json + md` 两种 catalog
- 至少能把 suite manifest 的 expected outputs 映射到产物来源
