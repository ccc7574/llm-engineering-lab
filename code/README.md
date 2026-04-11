# Code Map

这里的代码目录当前仍然以“阶段实现”组织，但在 V2 语义上，它已经开始映射到能力线:

- `stage0_bigram`、`stage1_nanogpt_core` -> `Track P: Pretraining`
- `stage2_sft`、`stage3_reasoning`、`stage4_verifier` -> `Track S: Post-Training`
- `stage5_toy_alignment` -> `Track S` 的后续部分

V2 目前已经把 `Coding`、`Multimodal`、`Agentic`、`Harness` 的 starter 实现接进这里，但仍然遵守“先把最小链路讲清楚，再增加复杂度”的原则。

## 目录约定

### `common`

项目共用的最小工具层。

建议包含:

- tokenizer
- JSONL 读写
- 随机种子和设备选择

### `stage0_bigram`

最小语言建模入口。

用途:

- 用极弱模型建立“next-token prediction”直觉
- 给完全没有模型背景的工程师一个最低门槛起点

### `stage1_nanogpt_core`

项目的核心教学内核，对应 `nanoGPT` 风格的最小 GPT 实现。

建议包含:

- `train.py`
- `sample.py`
- `model.py`
- `data.py`
- `debug_batch.py`
- `visualize_attention.py`

### `stage2_sft`

把 base model 改造成 instruction model 的最小实现。

当前已实现:

- `train_sft.py`
- `dataset.py`
- `prompt_template.py`

补充:

- 支持普通 instruction 数据和 reasoning 数据混合训练
- 会按样本长度自动扩展 `block_size`

### `stage3_reasoning`

推理时增强策略。

当前已实现:

- `sample_reasoning.py`
- `self_consistency.py`

补充:

- 支持同一批候选同时做 self-consistency 和 verifier rerank 对照

### `stage4_verifier`

候选答案评分和重排模块。

当前已实现:

- `model.py`
- `train_verifier.py`
- `rerank.py`
- `features.py`

### `stage5_toy_alignment`

极小规模偏好优化实验。

当前已实现:

- `dataset.py`
- `utils.py`
- `train_dpo.py`
- `train_grpo.py`

### `stage_coding`

Coding 能力线的最小入口。

当前已实现:

- `dataset.py`
- `prompt_template.py`
- `baseline_runner.py`
- `context_builder.py`
- `repo_context_runner.py`
- `bugfix_dataset.py`
- `bugfix_runner.py`
- `judge.py`
- `multifile_bugfix_dataset.py`
- `patch_runner.py`
- `testgen_dataset.py`
- `testgen_runner.py`
- `agentic_dataset.py`
- `agentic_runner.py`
- `swebench_dataset.py`
- `swebench_runner.py`
- `passk_dataset.py`
- `passk_runner.py`
- `execution.py`

用途:

- 演示代码补全任务格式
- 演示 execution-based eval 如何接入
- 演示 repo-level context 如何影响结果
- 演示 query-aware context packing 如何从仓库里选相关文件
- 演示 bugfix 任务的最小闭环
- 演示 code judge / verifier 如何在候选池里做 rerank
- 演示 multi-file patch protocol 如何覆盖跨文件修复
- 演示 test generation 如何区分 reference 和 hidden bug
- 演示 agentic coding loop 如何把检索、patch、跑测和 repair 串成闭环
- 演示 SWE-bench 风格任务如何从 issue + failing test output 做 triage 和修复
- 演示多候选 test-time sampling 如何把 coding 评测从 pass@1 推进到 pass@k

### `stage_harness`

Harness 能力线的最小入口。

当前已实现:

- `run_registry.py`
- `report_runs.py`
- `regression_compare.py`
- `summary_board.py`
- `gate_check.py`
- `suite_runner.py`
- `artifact_catalog.py`
- `baseline_snapshot.py`
- `failure_replay.py`
- `notification_digest.py`
- `notification_payloads.py`
- `notification_dispatch.py`
- `notification_delivery.py`
- `notification_route.py`
- `notification_route_matrix.py`
- `notification_route_diff.py`
- `notification_route_lint.py`
- `notification_policy_gate.py`
- `notification_dispatch_policy.py`
- `notification_review_summary.py`
- `trend_board.py`
- `release_note.py`
- `pr_comment.py`

用途:

- 扫描 `runs/` 下的训练资产
- 输出最小 checkpoint / config registry 视图
- 用 manifest 顺序执行跨能力线 regression suite
- 为 CI 提供 strict / require-ship 的统一 suite 入口
- 支持 changed-scope suite 和 step retry
- 从 suite / summary / gate 生成 notification digest
- 从 digest 生成 Slack / 飞书 payload
- 用 dry-run 或 webhook 发送通知 payload
- 基于 event / severity / gate 选择通知 channel
- 支持 route override 和更细粒度 failure taxonomy
- 生成 route matrix 作为 policy review artifact
- 比较 baseline vs candidate route matrix
- 对 route manifest 做 lint，对 route diff 做 gate
- 在 workflow 中执行 notification policy review/gate
- 判断当前 run 是否允许真实 dispatch
- 把 release gate、route gate 和 dispatch gate 压缩成 reviewer summary
- 生成 suite duration / cost drift 的 trend snapshot 与 board
- 支持 dispatch retry、幂等键和结构化 dispatch result artifact
- 生成 PR comment / release note 所需的统一 reviewer artifact
- 支持 provider-aware ack 解析和 channel-specific backoff 分类
- 支持 marker-based PR comment upsert 和结构化回写结果
- 支持 failure-category-aware route matching、matrix/diff 维度扩展与 policy gate 守门
- 支持 PR comment GitHub API 失败诊断和 markdown 结果摘要
- 支持 live webhook host 校验、Feishu secret 签名和 dispatch security artifact
- 支持 artifact catalog、baseline snapshot 和 failure replay plan，把产物治理和 task/sample 级失败重放都纳入标准链路
- 支持 notification delivery orchestration，把 route、dispatch policy 和 live dispatch 收敛到统一入口

### `stage_agentic`

Agentic 能力线的最小入口。

当前已实现:

- `dataset.py`
- `tools.py`
- `state.py`
- `task_runner.py`

用途:

- 演示 direct answer 与 tool use 的差异
- 演示多步工具链与最小过程指标
- 演示 state / memory 与 failure recovery 的最小可执行闭环
- 演示 draft / critique / revise 的最小 reflection 对照实验

### `stage_multimodal`

Multimodal 能力线的最小入口。

当前已实现:

- `dataset.py`
- `task_runner.py`

用途:

- 演示 text-only 与 vision-augmented 的差异
- 演示文档理解、图表推理、状态卡读取的最小评测
- 演示 noisy OCR、字段抽取和 structured pipeline 的差异
- 演示 multi-page routing、region grounding 和 grounded pipeline 的差异
- 演示 document workflow 如何把跨页字段、表格和 owner lookup 串成最终业务答案

## 编码原则

- 每个阶段尽量只新增一类复杂度
- 先让读者看懂，再考虑抽象层次
- 优先单文件或少文件结构，避免过早框架化
- 每个脚本都要对应一个明确工单
- 工具层只保留最小共用能力，避免抽象反客为主

## 当前限制

- 代码目录历史上使用 `code/` 作为顶层包名，这对脚本入口是可用的，但对部分交互式导入场景并不理想
- 当前仓库最成熟的仍是 `Pretraining` 与 `Post-Training` 两条实现链
- `Coding`、`Multimodal`、`Agentic`、`Harness` 已有 runnable starter path，但距离真实生产工作流仍有明显简化
