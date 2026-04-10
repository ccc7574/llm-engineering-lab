# S12: 做 Rejection Sampling 路线

## 背景

在很多真实团队里，先做 rejection sampling 往往比直接上偏好优化更现实，因为它更便宜、更容易诊断，也更容易向业务解释。

## 任务目标

- 从候选池里筛出高质量样本
- 构造更干净的后续训练数据
- 理解 rejection sampling 与 verifier、偏好优化的关系

## 业务与资源约束

- 优先最小实现
- 必须说明采样成本和筛选成本

## 代码改造点

- 可新增 `code/stage3_reasoning/` 或 `code/stage5_toy_alignment/` 中的采样筛选脚本
- `datasets/tiny_reasoning/`

## 交付标准

- 至少能生成候选并筛掉低质量输出
- 至少能形成再训练或再评测输入
- 能解释 rejection sampling 适用场景

## 原理补充

rejection sampling 是“先生成，再筛选，再利用筛选结果”的路线，常常是偏好优化前的低风险基线。

## 实验步骤

1. 生成多候选
2. 用规则或 verifier 筛选
3. 比较筛选前后表现

## 结果解读

如果筛选后显著改善，说明候选池质量足够；如果几乎没改善，说明问题不在筛选层。

## 线上风险

- 筛选规则过拟合
- 候选生成成本高于收益

## 复盘与延伸

- 对应 roadmap: `S12`
- 下一步进入 `S20-S21`

