# C11: 把 bugfix 升级到 multi-file patch protocol

## 背景

真实代码修复很少只改一个函数。常见情况是:

- helper 有 bug
- 调用方也写错了
- 改一个文件还不够，另一个文件也要跟着调整

## 任务目标

- 建立最小 multi-file bugfix 数据格式
- 对比 `single_file` 和 `patch_protocol`
- 让读者理解 patch recall 和 files touched 为什么重要

## 交付标准

- 至少有一组跨文件修复任务
- 至少记录 touched files 和 patch recall
- 至少能用执行测试验证 patch 是否真的修好
