# Eval

这个目录用于放每个 sprint 的最小评测脚本和对照结果。

原则很简单:

- 不做大而全 benchmark
- 每轮只验证当前任务最关心的问题
- 指标必须能支持工程决策

## 建议评测项

### Sprint 0

- loss 是否下降
- 采样输出是否明显优于随机噪声

### Sprint 1

- 上下文变化是否影响预测
- attention 可视化是否与案例直觉一致

### Sprint 2

- base model 和 SFT model 的指令跟随对比
- 结构化输出成功率

### Sprint 3

- greedy vs self-consistency 的正确率变化
- verifier 重排后的命中率变化
- 延迟和 token 成本变化

### Sprint 4

- 偏好优化前后输出选择倾向的变化
- 是否出现过拟合或风格塌缩

### Coding

- execution success rate
- pass@1 / pass@k
- average candidates sampled / first pass index
- syntax error rate
- failure type distribution
- repo context vs local-only 对照
- average selected context count
- average relevant context recall
- average context char count
- bugfix before vs after 对照
- judge rerank 的候选数与通过率
- multi-file patch 的 files touched 与 patch recall
- test generation 的 bug detection rate
- agentic coding 的 repo reads、test runs、repair success rate

### Harness

- baseline vs candidate regression 差异
- average generated tokens / verifier calls
- latency 与 token cost 的变化

### Agentic

- task success rate
- average tool calls
- average steps
- average state reads / writes
- average recovery attempts
- trace 可解释性

### Multimodal

- task success rate
- average visual tokens used
- average field match rate
- average observation / reasoning steps
- text-only vs vision-augmented 对照
- 字段抽取错误如何影响最终答案
