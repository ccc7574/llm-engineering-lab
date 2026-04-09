# C03: 把执行反馈接进 coding 评测，建立 execution-based eval

## 背景

团队已经发现代码看起来像样不代表真的能用。很多生成结果:

- 语法正确但测试不过
- 能跑但边界条件错
- 改好了一个地方，却破坏了另一个地方

这意味着 coding eval 必须尽快接入执行反馈。

## 任务目标

- 设计 execution-based eval 的最小闭环
- 区分“文本质量”和“代码行为质量”
- 给后续 coding verifier、agentic coding 建立评测底座

## 业务与资源约束

- 测试必须可重复
- 样本必须足够小，避免评测过慢
- 失败日志必须可读，便于反馈回模型

## 代码改造点

- `eval/`
- `code/common/`
- 可新增 `eval/coding_eval.py`

## 交付标准

- 至少能运行一组自动测试
- 至少输出 pass/fail 和失败日志
- 至少支持 pass@k 或 execution success rate

## 原理补充

execution feedback 的价值在于:

1. 它提供了比文本相似度更强的监督信号
2. 它能暴露很多表面上看不出的逻辑错误
3. 它是 coding agent 自修复循环的核心输入

## 实验步骤

1. 准备一组函数与测试
2. 让模型生成多个候选
3. 对每个候选执行测试
4. 统计 pass@1、pass@k、失败类型

## 结果解读

读者应该知道:

- coding 能力的真实门槛不在“生成”，而在“生成后验证”
- execution-based eval 是 coding 能力线的基础设施

## 线上风险

- 测试覆盖不足，导致假阳性
- 执行环境不一致，导致结果不可比
- 失败日志过长，反而污染反馈

## 复盘与延伸

下一步可以自然进入:

- `C10` coding judge / verifier
- `A00-A10` agentic coding 路线
