# Role Learning Paths

这个文件把 `LLM Engineering Lab` 按工程角色重新组织成可执行的 2 / 4 / 6 周路径。

如果 [learning_paths.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/learning_paths.md) 解决的是“按能力层怎么学”，那么这个文件解决的是“不同岗位的人应该优先学什么、做到什么程度”。

## 使用方式

- `2 周`: 建立共同语言，能跑通最小闭环
- `4 周`: 进入本岗位最常见的优化与评测问题
- `6 周`: 进入 production-minded 视角，开始做路线判断、回归和发布标准

## 路径 1: 后端工程师

适合:

- 需要把模型能力接进服务、工作流或内部平台的人
- 对接口、稳定性、集成成本更敏感的人

2 周目标:

- 看懂模型工程最小闭环
- 知道为什么只会调 prompt 不够
- 能解释 execution feedback、tool use、regression gate 的价值

建议顺序:

1. `P00-P03`
2. `S00-S02`
3. `C00-C03`
4. `A00-A02`
5. `H00-H03`

4 周目标:

- 能围绕代码、agent、服务集成做最小优化
- 能看懂 repo context、bugfix、reflection、route policy 这些能力为什么会影响业务稳定性

建议顺序:

1. `C10-C13`
2. `C20-C21`
3. `A10-A11`
4. `H10-H15`

6 周目标:

- 能参与真实上线标准设计
- 能和模型团队一起定义故障归因、回滚标准、PR gate 和成本边界

重点补强:

- `H20-H33`
- `cases/mid_company`
- `cases/small_team`

常见误区:

- 只看 API 成功率，不看模型回归
- 只关注 latency，不看失败恢复和错误分流
- 把“能集成”误认为“能稳定交付”

## 路径 2: 平台 / 基础设施工程师

适合:

- 负责训练/评测/发布基础设施、回归套件、通知链路的人
- 需要统一不同模型任务入口和交付标准的人

2 周目标:

- 建立对训练、评测、run registry、summary board 的整体理解
- 理解为什么模型团队最终会被 harness 能力限制

建议顺序:

1. `P00-P03`
2. `S00-S02`
3. `H00-H03`

4 周目标:

- 能维护回归 suite、gate、artifact 输出和通知策略
- 能把 coding、agentic、multimodal 三类评测放进同一条发布链

建议顺序:

1. `C10-C21`
2. `A10-A11`
3. `M03-M04`
4. `H10-H33`

6 周目标:

- 能把 baseline 治理、route policy、dispatch policy、安全边界和 release note 做成统一交付流程
- 能支持大厂级别的平台化标准

重点补强:

- `cases/bigtech/model_platform_playbook.md`
- `docs/ci_regression_guide_zh.md`
- `runs/summary_board.json`、`runs/gate_report.json` 一类 artifact 的解释与治理

常见误区:

- 只做 runner，不做可审阅 artifact
- 只做 CI 成功/失败，不做 failure taxonomy
- 只看主指标，不看成本和过程指标

## 路径 3: 应用 / 产品工程师

适合:

- 负责把模型能力快速转成产品价值的人
- 需要在质量、体验、延迟和成本之间做高频取舍的人

2 周目标:

- 理解 instruction tuning、structured output、tool use 的直接产品价值
- 能快速跑通一条“模型能力 -> workflow -> eval”闭环

建议顺序:

1. `S00-S02`
2. `A00-A02`
3. `M00-M02`
4. `H00-H03`

4 周目标:

- 能把 reflection、multimodal grounding、coding triage 这些能力和产品场景对应起来
- 能基于简单评测决定“该不该继续投”

建议顺序:

1. `S10-S12`
2. `A10-A11`
3. `M03-M04`
4. `C20-C21`

6 周目标:

- 能根据中型公司或小团队约束制定路线
- 能解释为什么某些需求应该靠 post-training，某些应该靠 workflow 或 harness

重点补强:

- `cases/mid_company/domain_copilot_playbook.md`
- `cases/small_team/api_first_playbook.md`
- `S20-S22`

常见误区:

- 把功能 demo 当成可上线能力
- 只看 top-line 成功率，不看失败样本
- 不区分模型改进、workflow 改进和评测改进

## 路径 4: MLE / 模型平台工程师

适合:

- 需要同时理解训练、后训练、评测和发布链的人
- 需要和研究、平台、应用多方协作的人

2 周目标:

- 跑通预训练到后训练的最小链路
- 建立对 eval、verifier、alignment、harness 的统一视角

建议顺序:

1. `P00-P12`
2. `S00-S12`
3. `H00-H03`

4 周目标:

- 能做针对性的后训练、coding、multimodal、agentic 优化
- 能解释结果提升来自哪里，成本又增加在哪里

建议顺序:

1. `S20-S22`
2. `C10-C21`
3. `M03-M04`
4. `A10-A11`

6 周目标:

- 能主导一条从训练、评测到发布的 production-minded 路线
- 能针对大厂、中厂、小团队做不同技术组合

重点补强:

- `P20`
- `H10-H33`
- 三类 `cases/`

常见误区:

- 只关注模型损失，不关注交付面指标
- 只看 benchmark，不看 regression 与 release 流程
- 把“研究上更强”直接等同于“团队里更值得做”

## 快速选路

- 如果你最关心服务稳定性与集成: 先走“后端工程师”
- 如果你最关心回归、发布、通知、治理: 先走“平台 / 基础设施工程师”
- 如果你最关心产品落地和 workflow: 先走“应用 / 产品工程师”
- 如果你最关心训练、评测和整体路线: 先走“MLE / 模型平台工程师”

## 建议的交付标准

完成任一路径后，至少应该能做到:

- 说清楚本岗位最相关的 5-8 个任务为什么重要
- 独立跑通对应的 starter path
- 能解释 2-3 个核心指标和 2-3 个常见失败模式
- 能把一个公司案例层映射到自己的工作约束
