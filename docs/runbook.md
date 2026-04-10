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

## `S20-S21`: Toy Alignment

当前仓库尚未实现 `code/stage5_toy_alignment/` 下的 DPO / GRPO 脚本。这个阶段目前只有任务文档和数据占位，还不能直接运行。

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

## `H19`: Notification Route Matrix

如果要导出当前 policy 的整体行为矩阵:

```bash
python3 code/stage_harness/notification_route_matrix.py \
  --routes manifests/notification_routes.json \
  --output runs/notification_route_matrix.json \
  --md-output runs/notification_route_matrix.md
```

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
