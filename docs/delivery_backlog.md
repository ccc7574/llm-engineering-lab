# Delivery Backlog

这个文件用于把当前仓库从“starter path 已成型”推进到“2026 可交付模型工程实验室”的剩余工作收敛成单一执行列表。

## P0: 必须优先完成

1. [done] 补齐 `Pretraining` 与 `Post-Training` 的新任务体系
   - 当前 `P*`、`S*` 新编号几乎没有实体任务文档，学习路径在这里断层。
   - 目标是把 `roadmap -> learning path -> task -> code` 串成闭环。

2. [done] 落地 `stage5_toy_alignment`
   - 当前 `S20-S21` 在路线图里存在，但 `code/stage5_toy_alignment/` 还是空目录。
   - 需要最小可运行的 DPO / GRPO 或 reward-guided update 脚本、数据格式和评测入口。

3. [done] 做厚三类公司案例层
   - `cases/bigtech`、`cases/mid_company`、`cases/small_team` 目前只有 README 骨架。
   - 需要把六条能力线分别映射成真实团队约束、路线差异和取舍模板。

4. [done] 补 `Harness` 的 live adapter 安全层
   - 当前 notification / dispatch 已很完整，但还缺 webhook 签名校验、secret 使用边界、provider 身份隔离。

## P1: 高价值深水区

5. [done] 补 `Multimodal` 的 grounding / multi-page doc pipeline
   - 当前已到 OCR 与 structured pipeline，但还缺 page routing、region grounding、表格链路。

6. 补 `Agentic` 的 reflection / agent eval
   - 当前到 state / recovery 为止，离真实团队常见的 planner-reflection-observer 仍差一层。

7. 补 `Coding` 的 SWE-bench 风格任务和 `pass@k`
   - 当前有 completion、bugfix、testgen、agentic coding，但还缺更像真实仓库工单的任务拆解。

8. 把 `Harness` 从 regression 扩到 golden artifacts 治理
   - 包括 baseline 版本化、artifact 生命周期、快照保真、失败样本回放。

## P2: 完整交付层

9. 把中英双语文档做成并行主线
   - 当前中文很完整，但英文交付面还不够体系化。

10. 增补角色导向学习路径
   - 让后端、平台、应用、MLE 四类工程师各自有一份 2-6 周的建议路线。

11. 为关键任务补更多可视化资产
   - 包括训练/评测架构图、路由图、案例决策图，而不只是文字说明。

## 当前执行顺序

按以下顺序推进:

1. `Agentic` reflection / eval
2. `Coding` SWE-bench 风格任务
3. 中英双语主线与角色导向路径
4. 更完整的 artifact / baseline 治理
