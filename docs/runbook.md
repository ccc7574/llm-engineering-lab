# Runbook

这个文件当前覆盖 V2 中已经可运行的六条 starter path。

## 快速开始

```bash
cd llm-engineering-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## `P00`: Bigram 基线

```bash
python3 code/stage0_bigram/train_bigram.py --max-iters 300
python3 code/stage0_bigram/sample_bigram.py --checkpoint runs/stage0_bigram/ckpt.pt --start "The "
```

## `P01-P03`: nanoGPT 风格最小内核

```bash
python3 code/stage1_nanogpt_core/train.py --max-iters 400
python3 code/stage1_nanogpt_core/sample.py --checkpoint runs/stage1_gpt/ckpt.pt --start "Incident "
python3 code/stage1_nanogpt_core/sample.py --checkpoint runs/stage1_gpt/ckpt.pt --start "If a ticket affects payments, treat it as " --compare-start "If a ticket affects search but has a workaround, treat it as " --max-new-tokens 24 --top-k 8 --report-path runs/stage1_gpt/context_compare.txt
python3 code/stage1_nanogpt_core/sample.py --checkpoint runs/stage1_gpt/ckpt.pt --start "deploy failed after migration" --compare-start "deploy recovered after migration" --context-window 16 --max-new-tokens 24 --top-k 8 --report-path runs/stage1_gpt/window_compare.txt
python3 code/stage1_nanogpt_core/debug_batch.py --data-path datasets/tiny_shakespeare/input.txt
python3 code/stage1_nanogpt_core/visualize_attention.py --checkpoint runs/stage1_gpt/ckpt.pt --prompt "Question: Why did the deploy fail?" --svg-output runs/stage1_gpt/attention_heatmap.svg
```

## `S00-S02`: 指令微调

```bash
python3 code/stage2_sft/train_sft.py --init-from runs/stage1_gpt/ckpt.pt --max-iters 300
python3 eval/sft_eval.py --checkpoint runs/stage2_sft/ckpt.pt --data-path datasets/tiny_sft/eval.jsonl
```

如果要把 reasoning trace 也并入 SFT 路线，可以直接把 `tiny_reasoning` 数据加入同一训练脚本。脚本会自动把 reasoning 样本转换成 assistant 样本，并按最长样本自动扩展 `block_size`:

```bash
python3 code/stage2_sft/train_sft.py \
  --init-from runs/stage1_gpt/ckpt.pt \
  --data-path datasets/tiny_sft/train.jsonl datasets/tiny_reasoning/train.jsonl \
  --eval-path datasets/tiny_sft/eval.jsonl datasets/tiny_reasoning/eval.jsonl \
  --out-dir runs/stage2_reasoning_trace
```

## `S10-S11`: 推理增强

```bash
python3 code/stage3_reasoning/sample_reasoning.py --checkpoint runs/stage2_sft/ckpt.pt --question "A ticket spends 12 minutes in triage and 18 minutes in repair. How long is the total?" --num-samples 5
python3 eval/reasoning_eval.py --checkpoint runs/stage2_sft/ckpt.pt --data-path datasets/tiny_reasoning/eval.jsonl --num-samples 5
```

如果要专门测试 reasoning trace 路线，建议把 Stage 3 checkpoint 换成 `runs/stage2_reasoning_trace/ckpt.pt` 或其他 reasoning-only checkpoint，再做对照。

如果要把 verifier 直接接到同一批候选上做比较，可以加上 `--verifier-checkpoint`:

```bash
python3 code/stage3_reasoning/sample_reasoning.py \
  --checkpoint runs/stage2_reasoning_only_longctx/ckpt.pt \
  --verifier-checkpoint runs/stage4_verifier/ckpt.pt \
  --question "A queue has 16 messages and 9 are processed. How many are left?" \
  --num-samples 5

python3 eval/reasoning_eval.py \
  --checkpoint runs/stage2_reasoning_only_longctx/ckpt.pt \
  --verifier-checkpoint runs/stage4_verifier/ckpt.pt \
  --data-path datasets/tiny_reasoning/eval.jsonl \
  --num-samples 5
```

注意: 当前 tiny 项目里，verifier 只能在“候选池里已经包含相对更好的答案”时起作用；如果 generator 本身没有采到正确候选，rerank 也无法补救。

## `S11`: Verifier

```bash
python3 code/stage4_verifier/train_verifier.py --max-iters 200 --eval-interval 50
python3 code/stage4_verifier/rerank.py --checkpoint runs/stage4_verifier/ckpt.pt --prompt-file datasets/tiny_verifier/demo_candidates.jsonl
```

当前 verifier 会同时使用:

- 候选文本的字符级表征
- 从 `prompt` 和 `Final Answer` 中提取的最小数值一致性特征

它不是通用 judge，而是面向当前 tiny arithmetic / reasoning 任务的最小 scorer。

## `S12`: Rejection Sampling Route

```bash
python3 eval/rejection_sampling_eval.py \
  --data-path datasets/tiny_reasoning_rejection/eval.jsonl \
  --strategy consensus \
  --report-path runs/post_training_rejection_consensus.json

python3 eval/rejection_sampling_eval.py \
  --data-path datasets/tiny_reasoning_rejection/eval.jsonl \
  --strategy rejection_sampling \
  --report-path runs/post_training_rejection_sampling.json \
  --accepted-output runs/post_training_rejection_accepts.jsonl

python3 code/stage_harness/regression_compare.py \
  --baseline-report runs/post_training_rejection_consensus.json \
  --candidate-report runs/post_training_rejection_sampling.json \
  --output runs/post_training_rejection_regression_diff.json
```

这条路径主要看:

- 为什么候选池里“有正确答案”还不等于最终链路会选中它
- rejection sampling 怎样提高 accepted set 的精度
- acceptance rate 和 precision 之间的取舍是否值得

## `S20-S21`: Toy Alignment

```bash
python3 code/stage5_toy_alignment/train_dpo.py \
  --data-path datasets/tiny_preferences/train.jsonl \
  --init-from runs/stage2_sft_smoke/ckpt.pt \
  --out-dir runs/stage5_dpo

python3 code/stage5_toy_alignment/train_grpo.py \
  --data-path datasets/tiny_preferences/train.jsonl \
  --init-from runs/stage2_sft_smoke/ckpt.pt \
  --out-dir runs/stage5_grpo

python3 eval/alignment_eval.py \
  --checkpoint runs/stage2_sft_smoke/ckpt.pt \
  --reference-checkpoint runs/stage2_sft_smoke/ckpt.pt \
  --data-path datasets/tiny_preferences/train.jsonl \
  --report-path runs/post_training_base_eval.json

python3 eval/alignment_eval.py \
  --checkpoint runs/stage5_dpo/ckpt.pt \
  --reference-checkpoint runs/stage2_sft_smoke/ckpt.pt \
  --data-path datasets/tiny_preferences/train.jsonl \
  --report-path runs/post_training_dpo_eval.json

python3 eval/alignment_eval.py \
  --checkpoint runs/stage5_grpo/ckpt.pt \
  --reference-checkpoint runs/stage2_sft_smoke/ckpt.pt \
  --data-path datasets/tiny_preferences/train.jsonl \
  --report-path runs/post_training_grpo_eval.json

python3 code/stage_harness/regression_compare.py \
  --baseline-report runs/post_training_base_eval.json \
  --candidate-report runs/post_training_dpo_eval.json \
  --output runs/post_training_dpo_regression_diff.json

python3 code/stage_harness/regression_compare.py \
  --baseline-report runs/post_training_base_eval.json \
  --candidate-report runs/post_training_grpo_eval.json \
  --output runs/post_training_grpo_regression_diff.json
```

这两条路线当前都是教学级最小实现:

- `train_dpo.py` 使用 pairwise DPO loss
- `train_grpo.py` 使用 reward-guided 的相对更新近似

重点不是追求大规模 alignment 效果，而是让读者看懂:

- chosen / rejected 对怎样变成训练信号
- reference model 为什么重要
- 偏好优化和 SFT、rejection sampling 的边界是什么
- chosen win rate、preference margin 和 drift 到底有没有改善

## `C00-C03`: Coding Starter Path

```bash
python3 code/stage_coding/baseline_runner.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic
python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy weak
python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic --report-path runs/coding_eval_heuristic.json
python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy local_only --report-path runs/repo_context_local_only.json
python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy contextual --report-path runs/repo_context_contextual.json
python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy retrieved --report-path runs/repo_context_retrieved.json
python3 eval/bugfix_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy buggy --report-path runs/bugfix_buggy.json
python3 eval/bugfix_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy heuristic --report-path runs/bugfix_heuristic.json
```

## `C10`: Coding Judge / Verifier Path

```bash
python3 eval/bugfix_judge_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy first_candidate --report-path runs/bugfix_judge_first_candidate.json
python3 eval/bugfix_judge_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy judge_rerank --report-path runs/bugfix_judge_rerank.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/bugfix_judge_first_candidate.json --candidate-report runs/bugfix_judge_rerank.json --output runs/bugfix_judge_regression_diff.json
```

## `C11`: Multi-File Patch Protocol

```bash
python3 eval/multifile_bugfix_eval.py --data-path datasets/tiny_multifile_bugfix/eval.jsonl --strategy single_file --report-path runs/multifile_bugfix_single_file.json
python3 eval/multifile_bugfix_eval.py --data-path datasets/tiny_multifile_bugfix/eval.jsonl --strategy patch_protocol --report-path runs/multifile_bugfix_patch_protocol.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/multifile_bugfix_single_file.json --candidate-report runs/multifile_bugfix_patch_protocol.json --output runs/multifile_bugfix_regression_diff.json
```

## `C12`: Test Generation

```bash
python3 eval/testgen_eval.py --data-path datasets/tiny_testgen/eval.jsonl --strategy weak --report-path runs/testgen_weak.json
python3 eval/testgen_eval.py --data-path datasets/tiny_testgen/eval.jsonl --strategy targeted --report-path runs/testgen_targeted.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/testgen_weak.json --candidate-report runs/testgen_targeted.json --output runs/testgen_regression_diff.json
```

## `C13`: Agentic Coding Repair Loop

```bash
python3 eval/agentic_coding_eval.py --data-path datasets/tiny_agentic_coding/eval.jsonl --strategy single_pass --report-path runs/agentic_coding_single_pass.json
python3 eval/agentic_coding_eval.py --data-path datasets/tiny_agentic_coding/eval.jsonl --strategy repair_loop --report-path runs/agentic_coding_repair_loop.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/agentic_coding_single_pass.json --candidate-report runs/agentic_coding_repair_loop.json --output runs/agentic_coding_regression_diff.json
```

## `C20`: SWE-bench 风格任务拆解

```bash
python3 eval/swebench_eval.py --data-path datasets/tiny_swebench_lite/eval.jsonl --strategy issue_localized --report-path runs/swebench_issue_localized.json
python3 eval/swebench_eval.py --data-path datasets/tiny_swebench_lite/eval.jsonl --strategy triage_loop --report-path runs/swebench_triage_loop.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/swebench_issue_localized.json --candidate-report runs/swebench_triage_loop.json --output runs/swebench_regression_diff.json
```

这条路径主要看:

- 只盯 entrypoint 文件为什么会错过共享 helper 的真正缺陷
- failing test output 是否真的驱动了后续 triage
- `avg_repo_reads`、`avg_test_runs`、`avg_patch_attempts` 和 `avg_triage_reads` 带来了多少额外搜索成本

## `C21`: pass@k 与 Candidate Sampling

```bash
python3 eval/coding_passk_eval.py --data-path datasets/tiny_coding_passk/eval.jsonl --strategy single_sample --k 3 --report-path runs/coding_passk_single_sample.json
python3 eval/coding_passk_eval.py --data-path datasets/tiny_coding_passk/eval.jsonl --strategy sample_k --k 3 --report-path runs/coding_passk_sample_k.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/coding_passk_single_sample.json --candidate-report runs/coding_passk_sample_k.json --output runs/coding_passk_regression_diff.json
```

这条路径主要看:

- greedy 第一发失败时，候选池里是否已经出现可通过实现
- `pass@1` 和 `pass@k` 的差距是否值得额外执行成本
- `avg_candidates_sampled`、`avg_execution_checks`、`avg_first_pass_index` 是否仍在团队可接受范围内

## `H01-H03`: Harness Starter Path

```bash
python3 code/stage_harness/report_runs.py --runs-dir runs
python3 code/stage_harness/report_runs.py --runs-dir runs --output runs/run_registry.json
python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy weak --report-path runs/coding_eval_weak.json
python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic --report-path runs/coding_eval_heuristic.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/coding_eval_weak.json --candidate-report runs/coding_eval_heuristic.json --output runs/coding_regression_diff.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/repo_context_local_only.json --candidate-report runs/repo_context_retrieved.json --output runs/repo_context_regression_diff.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/bugfix_buggy.json --candidate-report runs/bugfix_heuristic.json --output runs/bugfix_regression_diff.json
```

## `A00-A02`: Agentic Starter Path

```bash
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic/eval.jsonl --strategy direct --report-path runs/agentic_direct.json
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic/eval.jsonl --strategy tool_use --report-path runs/agentic_tool_use.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/agentic_direct.json --candidate-report runs/agentic_tool_use.json --output runs/agentic_regression_diff.json
```

## `A02-A10`: Agentic State / Recovery Path

```bash
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_memory/eval.jsonl --strategy tool_use --report-path runs/agentic_memory_tool_use.json
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_memory/eval.jsonl --strategy stateful --report-path runs/agentic_memory_stateful.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/agentic_memory_tool_use.json --candidate-report runs/agentic_memory_stateful.json --output runs/agentic_memory_regression_diff.json
```

## `A11`: Reflection / Agent Eval Path

```bash
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_reflection/eval.jsonl --strategy tool_use --report-path runs/agentic_reflection_tool_use.json
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_reflection/eval.jsonl --strategy reflective --report-path runs/agentic_reflection_reflective.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/agentic_reflection_tool_use.json --candidate-report runs/agentic_reflection_reflective.json --output runs/agentic_reflection_regression_diff.json
```

这条路径主要看:

- 第一版草稿为什么会错
- critique / revise 是否真的改善成功率
- `avg_reflection_steps` 带来了多少额外步骤成本

## `A12`: Planner / Observer Workflow Path

```bash
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_planner/eval.jsonl --strategy stateful --report-path runs/agentic_planner_stateful.json
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_planner/eval.jsonl --strategy planner_observer --report-path runs/agentic_planner_planner_observer.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/agentic_planner_stateful.json --candidate-report runs/agentic_planner_planner_observer.json --output runs/agentic_planner_regression_diff.json
```

这条路径主要看:

- memory / recovery 为什么还不能替代显式 planner
- observer check 怎样把“看起来能执行”的草稿，变成真正满足升级策略的输出
- `avg_planning_steps` 和 `avg_observer_checks` 带来了多少额外成本

## `M00-M02`: Multimodal Starter Path

```bash
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal/eval.jsonl --strategy text_only --report-path runs/multimodal_text_only.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal/eval.jsonl --strategy vision_augmented --report-path runs/multimodal_vision_augmented.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/multimodal_text_only.json --candidate-report runs/multimodal_vision_augmented.json --output runs/multimodal_regression_diff.json
```

## `M03`: Noisy OCR / Structured Pipeline Path

```bash
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_noisy/eval.jsonl --strategy ocr_only --report-path runs/multimodal_noisy_ocr_only.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_noisy/eval.jsonl --strategy structured_pipeline --report-path runs/multimodal_noisy_structured_pipeline.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/multimodal_noisy_ocr_only.json --candidate-report runs/multimodal_noisy_structured_pipeline.json --output runs/multimodal_noisy_regression_diff.json
```

## `M04`: Grounding / Multi-Page Pipeline

```bash
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_grounding/eval.jsonl --strategy ocr_only --report-path runs/multimodal_grounding_ocr_only.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_grounding/eval.jsonl --strategy grounded_pipeline --report-path runs/multimodal_grounding_grounded_pipeline.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/multimodal_grounding_ocr_only.json --candidate-report runs/multimodal_grounding_grounded_pipeline.json --output runs/multimodal_grounding_regression_diff.json
```

这条路径主要回答:

- 文档应该先看哪一页
- 当前问题应该落到哪个 region
- 为什么 `ocr_only` 常常会“看到了字，但看错了位置”

## `M05`: Document Workflow Pipeline

```bash
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_workflow/eval.jsonl --strategy grounded_pipeline --report-path runs/multimodal_workflow_grounded_pipeline.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_workflow/eval.jsonl --strategy document_pipeline --report-path runs/multimodal_workflow_document_pipeline.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/multimodal_workflow_grounded_pipeline.json --candidate-report runs/multimodal_workflow_document_pipeline.json --output runs/multimodal_workflow_regression_diff.json
```

这条路径主要回答:

- 只做 page / region grounding 为什么还不够
- 跨页表格和规则字段要怎样 join 成最终业务决策
- 为什么 owner / approver / escalation 这类答案天然要求 document workflow，而不是单页 OCR

## Cross-Track Summary

```bash
python3 code/stage_harness/summary_board.py --runs-dir runs --registry-path runs/run_registry.json --output runs/summary_board.json --md-output runs/summary_board.md
python3 code/stage_harness/gate_check.py --summary-board runs/summary_board.json --output runs/gate_report.json
```

## `H11`: Manifest-Driven Regression Suite

```bash
python3 code/stage_harness/suite_runner.py --manifest manifests/regression_v2_suite.json --output runs/regression_suite_report.json --md-output runs/regression_suite_report.md
```

如果要让 suite 在本地直接模拟 CI 放行规则，可以加上 `--strict --require-ship`:

```bash
python3 code/stage_harness/suite_runner.py --manifest manifests/regression_v2_suite.json --output runs/regression_suite_report.json --md-output runs/regression_suite_report.md --strict --require-ship
```

当前 suite 还会顺带生成:

- `runs/artifact_catalog.json`
- `runs/artifact_catalog.md`

## `H34`: Artifact Catalog And Lifecycle

```bash
python3 code/stage_harness/artifact_catalog.py \
  --runs-dir runs \
  --manifest manifests/regression_v2_suite.json \
  --policy-path manifests/artifact_lifecycle_policy.json \
  --output runs/artifact_catalog.json \
  --md-output runs/artifact_catalog.md
```

这条路径主要看:

- `runs/` 下哪些 artifact 应该作为发布证据保留
- 哪些 artifact 只是为了 replay 或调试
- suite manifest 的 expected outputs 是否和实际产物对得上

## `H35`: Baseline Snapshot Governance

```bash
python3 code/stage_harness/baseline_snapshot.py \
  --catalog runs/artifact_catalog.json \
  --label ship-ready-2026-04-10 \
  --output-root artifacts/baselines
```

如果你只想把更严格的 ship 证据固化成 baseline，也可以只保留 `promote_on_ship`:

```bash
python3 code/stage_harness/baseline_snapshot.py \
  --catalog runs/artifact_catalog.json \
  --label ship-only-2026-04-10 \
  --output-root artifacts/baselines \
  --include-lifecycle promote_on_ship
```

这条路径主要看:

- 哪些 artifact 被纳入 baseline
- 复制后的哈希是否一致
- snapshot 是否能作为未来 drift 对比的稳定参照

## `H36`: Failure Replay Plan

```bash
python3 code/stage_harness/failure_replay.py \
  --suite-report runs/regression_suite_report.json \
  --output runs/failure_replay_plan.json \
  --md-output runs/failure_replay_plan.md
```

这条路径主要看:

- 当前 suite 失败了哪些 step
- 每个 step 的 replay command 是什么
- 哪些 eval report 里已经能直接定位到失败 task / sample
- 生成的 task replay 是否已经自动改写成独立 `runs/replay/*.json` 输出

如果 suite 虽然整体通过，但你仍然想把弱策略里的失败样本逐个重放，这个 plan 也会继续列出 sample 级命令。例如:

```bash
python3 eval/coding_eval.py \
  --data-path datasets/tiny_coding/eval.jsonl \
  --strategy weak \
  --task-id reverse_string \
  --report-path runs/replay/coding_eval_weak__reverse_string.json
```

## `H12`: CI Launcher

仓库已带 GitHub Actions workflow:

```text
.github/workflows/regression-suite.yml
```

它会在 `pull_request`、`push(main)`、`workflow_dispatch` 和定时任务里执行同一条 suite，并上传:

- `runs/regression_suite_report.json`
- `runs/regression_suite_report.md`
- `runs/summary_board.json`
- `runs/summary_board.md`
- `runs/gate_report.json`

配套中文说明见 [ci_regression_guide_zh.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/ci_regression_guide_zh.md)。

## `H13`: Changed-Scope 与 Retry

如果要只按变更文件运行受影响能力线，可以先准备一个文件列表:

```bash
git diff --name-only HEAD^ HEAD > runs/changed_files.txt
```

然后执行:

```bash
python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --changed-files-path runs/changed_files.txt \
  --clean-regression-artifacts \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md \
  --strict
```

当前 manifest 默认给每个 step 1 次重试，suite report 会额外记录 `attempt_count`。

## `H14`: Notification Digest

在 suite、summary 和 gate 都生成后，可以进一步产出通知摘要:

```bash
python3 code/stage_harness/notification_digest.py \
  --suite-report runs/regression_suite_report.json \
  --summary-board runs/summary_board.json \
  --gate-report runs/gate_report.json \
  --output runs/notification_digest.json \
  --md-output runs/notification_digest.md
```

这个 artifact 适合:

- 值班摘要
- 发布前检查结论
- CI Job Summary 顶部摘要

## `H15`: External Notification Payloads

如果要进一步生成 Slack / 飞书 payload:

```bash
python3 code/stage_harness/notification_payloads.py \
  --digest runs/notification_digest.json \
  --slack-output runs/notification_slack.json \
  --feishu-output runs/notification_feishu.json
```

这一步不会真正发送消息，只会生成可直接外发的 payload artifact。

## `H16`: Notification Dispatch

如果要本地 dry-run 一次 dispatch:

```bash
python3 code/stage_harness/notification_dispatch.py \
  --payload runs/notification_slack.json \
  --channel slack_webhook \
  --webhook-url https://example.invalid/webhook \
  --dry-run
```

如果在真实环境里发送，可以去掉 `--dry-run`，并通过参数或环境变量提供:

- `SLACK_WEBHOOK_URL`
- `FEISHU_WEBHOOK_URL`

当前 dispatch 还支持:

- `--max-attempts`
- `--retry-delay-seconds`
- `--idempotency-key`
- `--signing-secret`
- `--state-path`
- `--output`

例如:

```bash
python3 code/stage_harness/notification_dispatch.py \
  --payload runs/notification_slack.json \
  --channel slack_webhook \
  --state-path runs/notification_dispatch_state.json \
  --output runs/notification_dispatch_result.json
```

这会带来两层保护:

- 遇到临时 webhook 错误时做最小重试
- 对同一 idempotency key 的成功发送做重复抑制

当前 dispatch result 还会额外记录:

- `provider`
- `ack_status`
- `failure_category`
- `security.webhook_source`
- `security.url_validation`
- `security.signed_request`
- `attempts[*].retryable`
- `attempts[*].next_delay_seconds`

并且不同 channel 会使用不同的 base backoff:

- `slack_webhook`: `1.0s`
- `feishu_webhook`: `1.5s`

当前 live adapter 还会做两层安全边界:

- `https` + provider host allowlist 校验
- `feishu_webhook` 在提供 `FEISHU_WEBHOOK_SECRET` 或 `--signing-secret` 时自动注入 `timestamp` 和 `sign`

## `H17`: Notification Routing Policy

如果要查看当前 digest 在不同事件下会路由到哪个通道:

```bash
python3 code/stage_harness/notification_route.py \
  --digest runs/notification_digest.json \
  --routes manifests/notification_routes.json \
  --event-name schedule \
  --default-channel none \
  --output runs/notification_route.json
```

这个步骤会产出:

- `channel`
- `reason`
- `payload_path`
- `matched_failure_categories`
- `top_failure_category`

如果要临时覆盖 route policy:

```bash
python3 code/stage_harness/notification_route.py \
  --digest runs/notification_digest.json \
  --routes manifests/notification_routes.json \
  --event-name workflow_dispatch \
  --default-channel none \
  --override-channel feishu_webhook \
  --output runs/notification_route.json
```

如果要让不同 failure category 直接走不同 channel，直接在 route manifest 里给 rule 增加:

- `failure_categories`

当前 `workflow_dispatch + warning/critical + hold/block` 场景下，`permission_error` 和 `report_parse_error` 会优先命中更高优先级的飞书规则。

## `H19`: Notification Route Matrix

如果要导出当前 policy 的整体行为矩阵:

```bash
python3 code/stage_harness/notification_route_matrix.py \
  --routes manifests/notification_routes.json \
  --output runs/notification_route_matrix.json \
  --md-output runs/notification_route_matrix.md
```

当前矩阵已经包含:

- `event`
- `severity`
- `gate`
- `failure_category`
- `ship_ready`
- `channel`
- `reason`

## `H21`: Notification Policy Regression

如果要比较 baseline 与 candidate policy 的实际路由变化:

```bash
python3 code/stage_harness/notification_route_matrix.py \
  --routes manifests/notification_routes_baseline.json \
  --output runs/notification_route_matrix_baseline.json \
  --md-output runs/notification_route_matrix_baseline.md

python3 code/stage_harness/notification_route_matrix.py \
  --routes manifests/notification_routes.json \
  --output runs/notification_route_matrix_candidate.json \
  --md-output runs/notification_route_matrix_candidate.md

python3 code/stage_harness/notification_route_diff.py \
  --baseline runs/notification_route_matrix_baseline.json \
  --candidate runs/notification_route_matrix_candidate.json \
  --output runs/notification_route_diff.json \
  --md-output runs/notification_route_diff.md
```

如果 candidate policy 只是在特定 failure category 下调整 channel，diff 也会按 `failure_category` 维度精确显示，不会把所有同 severity 的行混在一起。

## `H22`: Notification Policy Gate

对通知策略做 lint 和 gate:

```bash
python3 code/stage_harness/notification_route_lint.py \
  --routes manifests/notification_routes.json \
  --output runs/notification_route_lint.json

python3 code/stage_harness/notification_policy_gate.py \
  --route-diff runs/notification_route_diff.json \
  --policy manifests/notification_policy_gate.json \
  --output runs/notification_policy_gate.json
```

当前 gate allowlist 也已经按 `failure_category` 守门，所以“权限错误改走飞书”这类定向升级可以被显式批准，而不会放宽整段 severity 范围。

上面这条命令默认只生成 gate report，不会因为 `decision != ship` 直接退出失败。

如果要在 CI 里也强制执行这条 gate，workflow_dispatch 现在支持:

- `require_policy_gate=true`

如果要在本地显式模拟“非 ship 直接失败”的 enforcement 模式，可以加上:

```bash
python3 code/stage_harness/notification_policy_gate.py \
  --route-diff runs/notification_route_diff.json \
  --policy manifests/notification_policy_gate.json \
  --fail-on-non-ship
```

## `H24`: Notification Dispatch Policy

如果要区分“route 已经选好”和“这次 run 是否真的允许外发”，可以执行:

```bash
python3 code/stage_harness/notification_dispatch_policy.py \
  --digest runs/notification_digest.json \
  --route runs/notification_route.json \
  --policy manifests/notification_dispatch_policy.json \
  --event-name workflow_dispatch \
  --output runs/notification_dispatch_policy.json
```

当前默认策略是:

- `schedule` 允许向已路由的 Slack / 飞书通道真实发送
- `workflow_dispatch` 只有高严重度告警或显式 route override 时才允许真实发送
- 其他事件默认只生成 artifact，不直接 live dispatch

## `H37`: Notification Delivery Orchestration

如果要把 route、dispatch policy 和 live dispatch 串成一条统一入口，可以执行:

```bash
python3 code/stage_harness/notification_delivery.py \
  --digest runs/notification_digest.json \
  --routes manifests/notification_routes.json \
  --dispatch-policy manifests/notification_dispatch_policy.json \
  --event-name workflow_dispatch \
  --default-channel none \
  --state-path runs/notification_dispatch_state.json \
  --route-output runs/notification_route.json \
  --dispatch-policy-output runs/notification_dispatch_policy.json \
  --dispatch-result-output runs/notification_dispatch_result.json \
  --output runs/notification_delivery.json \
  --md-output runs/notification_delivery.md
```

这条路径会统一产出:

- `notification_route.json`
- `notification_dispatch_policy.json`
- `notification_dispatch_result.json`
- `notification_delivery.json`

它适合:

- 本地一次性模拟完整通知链
- CI 复用同一段 route / policy / dispatch 编排
- release owner 快速确认“这次有没有尝试发送、为什么没发送、最终状态是什么”

## `H25`: Notification Review Summary

如果要给 reviewer / release owner 产出压缩版审阅结论，可以执行:

```bash
python3 code/stage_harness/notification_review_summary.py \
  --digest runs/notification_digest.json \
  --route runs/notification_route.json \
  --policy-gate runs/notification_policy_gate.json \
  --dispatch-policy runs/notification_dispatch_policy.json \
  --output runs/notification_review_summary.json \
  --md-output runs/notification_review_summary.md
```

这个 artifact 会把:

- release gate
- route policy gate
- dispatch allow/deny
- failed steps / failure counts / active scopes

压成一张适合放在 GitHub Job Summary 顶部的卡片。

## `H26`: Latency / Cost Trend Board

如果要把当前 suite 的耗时热点和各能力线 cost drift 沉淀成 snapshot，可以执行:

```bash
python3 code/stage_harness/trend_board.py \
  --summary-board runs/summary_board.json \
  --suite-report runs/regression_suite_report.json \
  --snapshot-output runs/harness_trend_snapshot.json \
  --output runs/harness_trend_board.json \
  --md-output runs/harness_trend_board.md
```

如果手上已经有上一版 snapshot，也可以继续做趋势对比:

```bash
python3 code/stage_harness/trend_board.py \
  --summary-board runs/summary_board.json \
  --suite-report runs/regression_suite_report.json \
  --baseline-snapshot path/to/previous_harness_trend_snapshot.json \
  --snapshot-output runs/harness_trend_snapshot.json \
  --output runs/harness_trend_board.json \
  --md-output runs/harness_trend_board.md
```

这个 artifact 主要看三类信息:

- 当前 suite 总耗时和最慢 step
- 当前各 track 的 cost signal
- 相对上一版 snapshot 的 duration drift 和 cost drift

## `H28`: PR Comment / Release Note

如果要把 suite、review summary、trend board 和 dispatch 状态压成统一发布说明，可以执行:

```bash
python3 code/stage_harness/release_note.py \
  --summary-board runs/summary_board.json \
  --suite-report runs/regression_suite_report.json \
  --digest runs/notification_digest.json \
  --review-summary runs/notification_review_summary.json \
  --trend-board runs/harness_trend_board.json \
  --output runs/release_note.json \
  --md-output runs/release_note.md
```

如果本次 run 还产生了 dispatch result，也可以一并接入:

```bash
python3 code/stage_harness/release_note.py \
  --summary-board runs/summary_board.json \
  --suite-report runs/regression_suite_report.json \
  --digest runs/notification_digest.json \
  --review-summary runs/notification_review_summary.json \
  --trend-board runs/harness_trend_board.json \
  --dispatch-result runs/notification_dispatch_result.json \
  --output runs/release_note.json \
  --md-output runs/release_note.md
```

这个 artifact 适合:

- GitHub Job Summary 顶部总览
- 后续 PR comment bot
- release owner 的统一放行说明

## `H30`: PR Comment Writeback

如果要把 `release_note.md` 真正写回 GitHub PR comment，可以执行:

```bash
python3 code/stage_harness/pr_comment.py \
  --repo owner/repo \
  --pr-number 123 \
  --body-path runs/release_note.md \
  --dry-run \
  --output runs/pr_comment_result.json \
  --md-output runs/pr_comment_result.md
```

真实写回时去掉 `--dry-run`，并提供:

- `GITHUB_TOKEN` 或 `GH_TOKEN`

这个脚本会:

- 用 marker 识别是否已有机器人评论
- 已有则 update，没有则 create
- 在缺 token 或权限不足时保留 result artifact，而不是强行拖挂整条 suite
- 给 `403 / 404 / 422` 等 GitHub API 失败返回结构化 diagnosis 和 actionable hint

## `H31`: Failure-Category-Aware Routing

如果要验证 failure taxonomy 是否已经真实联动 route policy，可以执行:

```bash
python3 code/stage_harness/notification_route_lint.py \
  --routes manifests/notification_routes.json \
  --output runs/notification_route_lint.json

python3 code/stage_harness/notification_route_matrix.py \
  --routes manifests/notification_routes_baseline.json \
  --output runs/notification_route_matrix_baseline.json \
  --md-output runs/notification_route_matrix_baseline.md

python3 code/stage_harness/notification_route_matrix.py \
  --routes manifests/notification_routes.json \
  --output runs/notification_route_matrix_candidate.json \
  --md-output runs/notification_route_matrix_candidate.md

python3 code/stage_harness/notification_route_diff.py \
  --baseline runs/notification_route_matrix_baseline.json \
  --candidate runs/notification_route_matrix_candidate.json \
  --output runs/notification_route_diff.json \
  --md-output runs/notification_route_diff.md

python3 code/stage_harness/notification_policy_gate.py \
  --route-diff runs/notification_route_diff.json \
  --policy manifests/notification_policy_gate.json \
  --output runs/notification_policy_gate.json
```

这条链路主要回答三件事:

- digest 里的 `top_failure_category` 有没有进入 route 决策
- route diff 是否只改变了目标 failure category 对应的行
- policy gate 是否只放行团队明确批准的分类级别路由变更

## 2026 V2 说明

从 V2 开始，这个仓库的主入口应以:

1. [project_charter.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/project_charter.md)
2. [roadmap_v2.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/roadmap_v2.md)
3. [learning_paths.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/learning_paths.md)

为准。

本文件负责“怎么运行现有实现”，而不是负责定义整个项目的长期路线。

## 注意事项

- 所有脚本默认针对极小数据集和极小模型，只为教学和研发演练服务
- 如果机器没有 GPU，默认会退回 CPU
- 如果 `runs/` 里没有对应 checkpoint，请先执行上一阶段训练
- 当前代码目录仍沿用 `code/` 命名，执行脚本时请优先使用仓库里给出的脚本入口，避免自行从仓库根目录运行临时 `python -c` 导入检查
