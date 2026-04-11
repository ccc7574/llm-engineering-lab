# A20: 把 agent 能力映射到 browser / office workflow

## 背景

很多团队真正愿意为 agent 买单的，不是“多会聊天”，而是它能不能稳定完成:

- 查资料
- 填表
- 抽取信息
- 生成邮件 / 周报 / 审批说明
- 跨 browser 和 office 工具完成一次业务闭环

这类任务的难点通常不在单个工具调用，而在权限、上下文切换、失败恢复和人工接管边界。

## 任务目标

- 为 browser / office workflow 设计最小任务集
- 明确 planner、memory、observer 在办公任务中的角色分工
- 定义人工接管点、审批点和失败恢复点

## 业务与资源约束

- 必须贴近真实工作流，而不是抽象对话
- 必须显式考虑权限和审计边界
- 必须允许失败后人工接管

## 代码改造点

- `code/stage_agentic/`
- `datasets/tiny_agentic_*`
- 可新增 browser / office 任务模拟器或 artifact 规范

## 交付标准

- 至少定义一组 browser workflow 任务
- 至少定义一组 office 文档 / 邮件 / 审批任务
- 至少记录 task success、step efficiency、handoff 点
- 至少给出“什么时候必须人审”的规则

## 原理补充

office / browser agent 的真正门槛，不是工具数量，而是:

- 状态是否可恢复
- 输出是否可审计
- 权限是否可控
- 人工接管是否自然

## 实验步骤

1. 先用 `A00-A12` 的最小 agent 框架定义浏览器和办公任务
2. 明确 plan / execute / observe / handoff 四段边界
3. 记录失败样本并归纳人工接管标准

## 结果解读

如果 agent 只是“偶尔做对一次”，但没有明确 handoff 和审计边界，那它仍然不算可交付 workflow。

## 线上风险

- 权限范围过大
- 浏览器状态漂移导致步骤复现困难
- 输出看似完整但实际缺少关键审批信息

## 复盘与延伸

- 对应 roadmap: `A20`
- 后续可以把 browser / office workflow 接进更真实的 benchmark 和 replay 机制
