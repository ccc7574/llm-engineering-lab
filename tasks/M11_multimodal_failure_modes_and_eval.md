# M11: 把多模态失败模式整理成可回归的 failure pack

## 背景

多模态系统在真实团队里最容易出现的误判，不是简单的“看不见图片”，而是:

- OCR 字段读到了，但字段语义错了
- page routing 对了，但 region grounding 错了
- grounding 对了，但跨页 join 漏了
- route policy 置信度看起来很高，但 dispatch 到了错误专家链路

如果这些失败只停留在口头复盘里，团队很快会重复踩同一类坑。

## 任务目标

- 设计多模态 failure taxonomy
- 把代表性误路由、误抽取、误 grounding、误 join 样本沉淀成 failure pack
- 让 failure pack 能进入 regression / replay / reviewer 总结

## 业务与资源约束

- 不追求大而全 benchmark
- failure pack 必须小而可审计
- 每类失败都要能明确映射到具体链路层

## 代码改造点

- `datasets/`
- `eval/`
- `code/stage_harness/`
- 可新增 replay / failure bucket artifact

## 交付标准

- 至少定义 4 类多模态失败类型
- 至少有一组 route-policy 误路由样本
- 至少有一组 document workflow join 失败样本
- 至少能输出 reviewer 可读的 failure summary

## 原理补充

多模态工程里，真正影响团队效率的不是平均正确率，而是“哪一层最容易错、错了之后怎么快速重放和归因”。

## 实验步骤

1. 先从 `M03-M05` 和 `M10` 的失败样本里抽 bucket
2. 给每个 bucket 标上链路层级和预期修复方向
3. 把它们接入 failure replay 或专项 eval

## 结果解读

理想结果不是“失败为零”，而是团队能把失败快速定位成:

- 数据问题
- router 问题
- OCR / parsing 问题
- workflow join 问题

## 线上风险

- 只记录最终答案错误，不记录中间链路错误
- failure taxonomy 太粗，导致修复建议没有操作性

## 复盘与延伸

- 对应 roadmap: `M11`
- 可以直接复用 `M10` 的误路由样本做第一版 failure pack
