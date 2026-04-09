# H12: 把 regression suite 接进 CI launcher

## 背景

很多仓库会在本地写出一条很好看的回归命令，但真正到团队协作时，这条命令并没有进入 PR、push 或定时巡检流程。

这会导致一个常见问题:

- 本地能跑
- 团队没人固定去跑
- 发布前还是回到人工检查

## 任务目标

- 给 regression suite 增加 CI 严格模式
- 建立 GitHub Actions workflow，让 suite 能在 PR、主分支和定时任务里运行
- 把 suite report 和 summary board 作为 CI artifact 保留下来

## 交付标准

- 至少有一条 workflow 可以执行 suite manifest
- 至少能在 suite 失败或 gate 非 `ship` 时让 CI 失败
- 至少上传 suite report / summary board / gate report artifact
