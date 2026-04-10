# S11: 用 Self-Consistency 与 Verifier 提升结果选择

## 背景

很多场景里模型不是完全不会，而是会在多个候选里有好有坏。这时最值得做的，不一定是重新训练，而是改采样和筛选。

## 任务目标

- 比较单样本和多样本采样
- 引入 verifier / reranker
- 区分 generator 改进和 selector 改进

## 业务与资源约束

- 候选数不能无限增大
- 必须同时衡量成本和收益

## 代码改造点

- `code/stage3_reasoning/sample_reasoning.py`
- `code/stage4_verifier/train_verifier.py`
- `code/stage4_verifier/rerank.py`
- `eval/reasoning_eval.py`

## 交付标准

- 至少比较 single-sample vs self-consistency
- 至少比较 no-verifier vs verifier-rerank
- 能说明 verifier 的边界

## 原理补充

verifier 只能在候选池里已有较好答案时起作用，它不是凭空创造正确答案的模块。

## 实验步骤

1. 生成多候选
2. 用 verifier 排序
3. 跑 reasoning eval 比较收益

## 结果解读

如果正确候选覆盖率不高，先改 generator；如果覆盖率高但首选不稳，再改 selector。

## 线上风险

- 候选数过多导致成本失控
- verifier overfit 到训练格式

## 复盘与延伸

- 对应旧任务: `T20` 与 `T21`
- 下一步进入 `S12`

