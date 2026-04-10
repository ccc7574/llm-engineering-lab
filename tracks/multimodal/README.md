# Track M: Multimodal

这个能力线负责解释图文联合能力、多模态后训练和多模态评测。

重点问题:

- OCR、文档理解、图表推理为什么不是一回事
- multimodal instruction tuning 改了什么
- 视觉 grounding 与文字问答的差异是什么

当前状态:

- 已有 `tiny_multimodal` 数据、SVG 视觉样本、task runner 和 `eval/multimodal_eval.py`
- 已形成 text-only vs vision-augmented 的最小对照实验
- 已形成 `ocr_only` vs `structured_pipeline` 的 noisy OCR / document pipeline 对照实验
- 已形成 `ocr_only` vs `grounded_pipeline` 的 multi-page / region grounding 对照实验

建议首批任务:

- `M00` 图文问答闭环
- `M01` 文档理解
- `M02` 图表与表格推理
- `M03` noisy OCR pipeline
- `M04` grounding and multi-page pipeline

当前可直接运行的最小命令见 [runbook.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/runbook.md)。
