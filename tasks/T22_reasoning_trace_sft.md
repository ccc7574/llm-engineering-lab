# T22: 用带中间过程的数据让模型更会解释

## 背景

当团队说“模型需要更会推理”时，很多时候真正想要的是两件事: 一是正确率更高，二是答案里有足够可审核的依据。这个工单聚焦第二件事。

## 任务目标

- 为 reasoning 样本引入中间步骤
- 观察带 trace 和不带 trace 的输出差异
- 让读者理解 trace 是一种数据格式和行为塑形手段

## 业务约束

- trace 不能过长
- 最终答案必须可提取
- 要能区分“会解释”和“真的更准”

## 你需要改的代码

- `datasets/tiny_reasoning/train.jsonl`
- `code/stage2_sft/dataset.py`
- `code/stage3_reasoning/sample_reasoning.py`

## 交付标准

- 至少一组带 rationale 的训练样例
- 生成结果中包含可解析的最终答案
- 对比 trace 对正确率和可读性的影响

