# C12: 让模型学会生成能抓住 bug 的测试，而不是只写样子货

## 背景

很多自动测试生成看起来很热闹，但实际价值很低，因为它们:

- 只覆盖 happy path
- 不验证真正容易出错的边界
- 无法区分参考实现和隐藏 bug

## 任务目标

- 建立最小 test generation 路线
- 对比 `weak` 和 `targeted` 测试生成
- 用 bug detection rate 而不是“断言数量”做评估

## 交付标准

- 至少有一组参考实现与隐藏 bug 实现
- 至少能验证生成测试是否通过 reference 且抓住 bug
- 至少输出 `bug_detection_rate`
