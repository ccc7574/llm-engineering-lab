# M04: 做 grounding 与 multi-page document pipeline

## 背景

真实文档理解经常不是“看这一页回答一个问题”，而是:

- 先决定该看哪一页
- 再决定该看哪个区域
- 最后才从局部结构里提取业务答案

如果没有 page routing 和 region grounding，多模态系统很容易在“看见了文档”但“看错了位置”这一层出错。

参考图:

- [multimodal_grounding_pipeline.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/multimodal_grounding_pipeline.svg)

## 任务目标

- 增加 multi-page document routing 任务
- 增加 region grounding 任务
- 让 `ocr_only` 与 `grounded_pipeline` 做明确对照

## 交付标准

- 至少有一个跨页任务
- 至少有一个区域级 grounding 任务
- 至少让新任务进入统一 eval 与 regression suite
- 至少记录 page / region 级抽取字段
