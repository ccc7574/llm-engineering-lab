# M05: 把多页文档、表格归一和业务决策串成 document workflow pipeline

## 背景

真实多模态项目里，很多高价值任务并不是“从一张图里读一个答案”，而是:

- 先路由到正确页面
- 再把 noisy OCR / 表格行列归一
- 再把字段和规则页、审批页、路由页串起来
- 最后才返回业务 owner 或 action

如果只做到 grounding，团队通常还是会在“看对了位置，但没有把多页证据组合起来”这一层失效。

参考图:

- [multimodal_document_workflow.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/multimodal_document_workflow.svg)
- [multimodal_invoice_ops_packet.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/multimodal_invoice_ops_packet.svg)
- [multimodal_latency_escalation_packet.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/multimodal_latency_escalation_packet.svg)

## 任务目标

- 新增 document workflow 级多模态数据集
- 增加 `grounded_pipeline` 对 `document_pipeline` 的明确对照
- 让系统必须组合跨页表格、规则字段和最终 owner lookup

## 交付标准

- 至少有一组需要跨页 join 的文档任务
- 至少记录字段匹配率和最终任务成功率
- 至少让 `document_pipeline` 在 workflow 任务上优于 `grounded_pipeline`
- 至少把新路线接入统一 eval 与 regression suite
