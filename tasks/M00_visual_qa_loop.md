# M00: 跑通图文问答最小闭环，理解多模态不是“再多几行 OCR”

## 背景

很多工程师第一次做多模态时，会把它理解成“先 OCR，再让模型回答问题”。这只是多模态的一部分。真实工程里，多模态的关键在于如何把视觉观察转成稳定可评测的输入。

## 任务目标

- 建立图文问答的最小闭环
- 展示 text-only 和 vision-augmented 的差异
- 为后续文档理解和图表推理打基础

## 业务与资源约束

- 优先本地可跑
- 先聚焦结构清晰的小视觉任务
- 先讲任务格式和评测，不追求模型上限

## 代码改造点

- `code/stage_multimodal/`
- `datasets/tiny_multimodal/`
- `eval/multimodal_eval.py`

## 交付标准

- 至少包含一种视觉问答任务
- 至少有 text-only 与 vision-augmented 对照
- 至少统计 task success rate

## 线上风险

- OCR 信息不完整
- 视觉字段抽取错位
- 团队把“看见了图”误认为“理解了图”
