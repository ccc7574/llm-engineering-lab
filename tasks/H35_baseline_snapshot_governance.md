# H35: 把关键 artifact 固化成版本化 baseline snapshot

## 背景

只有 regression diff 还不够。

真实团队还需要回答:

- 这次准备推广的基线到底是哪一版
- 哪些 artifact 构成了这次发布前证据
- 未来 drift 对比时，应该拿哪一套快照做参考

## 任务目标

- 把关键 artifact 固化到版本化目录
- 保留哈希、来源和生命周期信息
- 让 baseline 不再只是“某个文件名里写着 baseline”

## 交付标准

- 至少支持从 artifact catalog 生成 snapshot
- 至少输出 `manifest.json`
- 至少验证复制后哈希一致
