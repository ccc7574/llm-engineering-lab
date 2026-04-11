# H20: 用统一周报与复盘模板把实验、回归和发布信息沉淀下来

## 背景

很多模型团队的问题不是“没有产物”，而是:

- 训练、评测、回归、发布信息分散在不同文件里
- 一周做了很多实验，但没人能快速说清楚真正值得继续投的路线
- reviewer 只能看零散截图，无法判断收益、成本和风险

所以 `H20` 不是再加一个报告文件，而是把模型工程周报做成统一模板。

参考模板:

- [model_engineering_weekly_review_template.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/model_engineering_weekly_review_template.md)
- [model_engineering_weekly_review_template_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/model_engineering_weekly_review_template_en.md)

## 任务目标

- 设计统一周报与复盘模板
- 把实验结论、回归结果、失败样本、下周动作放进同一结构
- 让大厂、中型公司、小团队都能按同一模板裁剪使用

## 业务与资源约束

- 模板必须面向工程执行，而不是宣传汇报
- 必须同时包含收益、成本、风险
- 必须能引用现有 artifact，而不是要求手工重复整理

## 代码改造点

- `docs/`
- `runs/`
- `code/stage_harness/`

## 交付标准

- 至少提供一份中文模板
- 最好同步提供英文模板
- 至少包含本周目标、关键变更、核心指标、失败样本、发布结论、下周计划
- 至少能直接引用 summary board / gate / replay plan / release note

## 原理补充

团队真正可持续的节奏，不是“每周都做新东西”，而是“每周都能把结果沉淀成下周可执行的判断”。

## 实验步骤

1. 先从现有 `runs/` 产物里挑出最关键 artifact
2. 设计一个 reviewer 能在 10 分钟内读完的模板
3. 按公司规模给出不同裁剪方式

## 结果解读

好模板的标准不是看起来完整，而是:

- 能快速回答“这周到底变好了没有”
- 能快速回答“为什么变好或变坏”
- 能快速回答“下周该继续投哪条路线”

## 线上风险

- 把周报写成流水账
- 只有 top-line 指标，没有失败样本
- 只写结果，不写下周明确动作

## 复盘与延伸

- 对应 roadmap: `H20`
- 后续可以把模板接到自动周报生成和 release review 工作流
