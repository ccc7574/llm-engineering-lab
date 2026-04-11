# Datasets

所有数据都故意做得很小，目标是让工程师能在单机上快速跑完一轮实验。

## 数据目录

- `tiny_shakespeare/input.txt`
  - 预训练用小文本，包含少量工程场景描述和自然语言样本
- `tiny_sft/train.jsonl`
  - 指令微调用小样本
- `tiny_sft/eval.jsonl`
  - SFT 评测小样本
- `tiny_reasoning/train.jsonl`
  - 带推理过程的小任务集
- `tiny_reasoning/eval.jsonl`
  - 推理增强评测集
- `tiny_reasoning_rejection/eval.jsonl`
  - rejection sampling 候选池回放数据，用于演示 consensus vs filter-and-accept
- `tiny_verifier/train.jsonl`
  - verifier 训练样本
- `tiny_verifier/demo_candidates.jsonl`
  - rerank 演示样本
- `tiny_preferences/train.jsonl`
  - DPO / toy alignment 配对数据
- `tiny_coding/train.jsonl`
  - coding 任务训练样本
- `tiny_coding/eval.jsonl`
  - coding execution-based eval 样本
- `tiny_repo_context/eval.jsonl`
  - repo-level context coding 样本
- `tiny_bugfix/train.jsonl`
  - bugfix 训练样本
- `tiny_bugfix/eval.jsonl`
  - bugfix 评测样本
- `tiny_multifile_bugfix/eval.jsonl`
  - multi-file patch bugfix 评测样本
- `tiny_testgen/eval.jsonl`
  - 测试生成与 hidden bug 检测评测样本
- `tiny_agentic_coding/eval.jsonl`
  - agentic coding 检索、补丁、跑测与自修复评测样本
- `tiny_agentic/eval.jsonl`
  - agentic 工具调用与多步执行评测样本
- `tiny_agentic_memory/eval.jsonl`
  - agentic 状态管理与失败恢复评测样本
- `tiny_multimodal/eval.jsonl`
  - 多模态图文问答与图表/文档理解评测样本
- `tiny_multimodal_noisy/eval.jsonl`
  - 带 OCR 噪声的发票、路由表和延迟表评测样本
- `tiny_multimodal_grounding/eval.jsonl`
  - 多页 routing / region grounding 评测样本
- `tiny_multimodal_workflow/eval.jsonl`
  - document workflow 级跨页 join 与 owner lookup 评测样本
- `tiny_multimodal_sft/train.jsonl`
  - 多模态 route-policy SFT 训练样本
- `tiny_multimodal_sft/eval.jsonl`
  - 带 `target_strategy` 标签的多模态 route-policy SFT 评测样本
- `tiny_pretraining_general/input.txt`
  - 通用预训练小语料
- `tiny_pretraining_payments/input.txt`
  - payments 领域 continued pretraining 小语料
- `tiny_pretraining_mixture/uniform.json`
  - 通用/领域均匀混合 manifest
- `tiny_pretraining_mixture/domain_heavy.json`
  - 领域偏置混合 manifest

## 格式约定

### SFT 数据

```json
{"instruction": "...", "input": "...", "output": "..."}
```

### Reasoning 数据

```json
{"question": "...", "rationale": "...", "answer": "..."}
```

`code/stage2_sft/train_sft.py` 现在可以直接读取这种格式，并自动转换成带 trace 的 assistant 输出:

```text
Reasoning: ...
Final Answer: ...
```

### Preference 数据

```json
{"prompt": "...", "chosen": "...", "rejected": "..."}
```

### Coding 数据

```json
{
  "task_id": "...",
  "instruction": "...",
  "starter_code": "...",
  "entry_point": "...",
  "canonical_solution": "...",
  "tests": ["assert ...", "assert ..."]
}
```
