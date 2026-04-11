# Runbook

This file is the English runnable guide for the current V2 lab.

It focuses on how to run the existing tracks, compare baseline vs candidate behavior, and inspect release-facing artifacts.

## Quick Start

```bash
cd llm-engineering-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## `P00-P03`: Minimal Pretraining Core

```bash
python3 code/stage0_bigram/train_bigram.py --max-iters 300
python3 code/stage0_bigram/sample_bigram.py --checkpoint runs/stage0_bigram/ckpt.pt --start "The "

python3 code/stage1_nanogpt_core/train.py --max-iters 400
python3 code/stage1_nanogpt_core/sample.py --checkpoint runs/stage1_gpt/ckpt.pt --start "Incident "
python3 code/stage1_nanogpt_core/debug_batch.py --data-path datasets/tiny_shakespeare/input.txt
python3 code/stage1_nanogpt_core/visualize_attention.py --checkpoint runs/stage1_gpt/ckpt.pt --prompt "Question: Why did the deploy fail?" --svg-output runs/stage1_gpt/attention_heatmap.svg
```

Use this path to build intuition about tokenization, next-token loss, context usage, and attention behavior before moving into optimization work.

## `P10-P12`: Pretraining Optimization Knobs

Read these tasks together with the core pretraining loop:

- [P10_data_mixture_and_sampling.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P10_data_mixture_and_sampling.md)
- [P11_continued_pretraining_and_domain_adaptation.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P11_continued_pretraining_and_domain_adaptation.md)
- [P12_context_length_extension.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/P12_context_length_extension.md)

The key engineering lesson is that data mixture, domain weighting, and context policy are usually more actionable than architecture changes in small and mid-scale teams.

## `S00-S02`: Instruction Tuning

```bash
python3 code/stage2_sft/train_sft.py --init-from runs/stage1_gpt/ckpt.pt --max-iters 300
python3 eval/sft_eval.py --checkpoint runs/stage2_sft/ckpt.pt --data-path datasets/tiny_sft/eval.jsonl
```

If you want to blend in reasoning traces:

```bash
python3 code/stage2_sft/train_sft.py \
  --init-from runs/stage1_gpt/ckpt.pt \
  --data-path datasets/tiny_sft/train.jsonl datasets/tiny_reasoning/train.jsonl \
  --eval-path datasets/tiny_sft/eval.jsonl datasets/tiny_reasoning/eval.jsonl \
  --out-dir runs/stage2_reasoning_trace
```

## `S10-S12`: Reasoning and Verifier Route

```bash
python3 code/stage3_reasoning/sample_reasoning.py --checkpoint runs/stage2_sft/ckpt.pt --question "A ticket spends 12 minutes in triage and 18 minutes in repair. How long is the total?" --num-samples 5
python3 eval/reasoning_eval.py --checkpoint runs/stage2_sft/ckpt.pt --data-path datasets/tiny_reasoning/eval.jsonl --num-samples 5

python3 code/stage4_verifier/train_verifier.py --max-iters 200 --eval-interval 50
python3 code/stage4_verifier/rerank.py --checkpoint runs/stage4_verifier/ckpt.pt --prompt-file datasets/tiny_verifier/demo_candidates.jsonl
```

Use this path to show that better reasoning is often a pipeline question: generator quality, candidate diversity, verifier behavior, and rerank discipline all matter.

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
```

These scripts are deliberately small. The point is to make preference signals, reference anchoring, and update tradeoffs visible to non-research engineers.

## `C00-C21`: Coding Evaluation Ladder

```bash
python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy weak --report-path runs/coding_eval_weak.json
python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic --report-path runs/coding_eval_heuristic.json
python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy retrieved --report-path runs/repo_context_retrieved.json
python3 eval/bugfix_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy heuristic --report-path runs/bugfix_heuristic.json
python3 eval/bugfix_judge_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy judge_rerank --report-path runs/bugfix_judge_rerank.json
python3 eval/multifile_bugfix_eval.py --data-path datasets/tiny_multifile_bugfix/eval.jsonl --strategy patch_protocol --report-path runs/multifile_bugfix_patch_protocol.json
python3 eval/testgen_eval.py --data-path datasets/tiny_testgen/eval.jsonl --strategy targeted --report-path runs/testgen_targeted.json
python3 eval/agentic_coding_eval.py --data-path datasets/tiny_agentic_coding/eval.jsonl --strategy repair_loop --report-path runs/agentic_coding_repair_loop.json
python3 eval/swebench_eval.py --data-path datasets/tiny_swebench_lite/eval.jsonl --strategy triage_loop --report-path runs/swebench_triage_loop.json
python3 eval/coding_passk_eval.py --data-path datasets/tiny_coding_passk/eval.jsonl --strategy sample_k --k 3 --report-path runs/coding_passk_sample_k.json
```

This track teaches that code quality depends on more than generation quality:

- repo context quality
- execution feedback
- judge and verifier quality
- multi-file patch protocol
- candidate sampling economics

## `A00-A11`: Agentic Tool Use, Memory, Reflection

```bash
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic/eval.jsonl --strategy tool_use --report-path runs/agentic_tool_use.json
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_memory/eval.jsonl --strategy stateful --report-path runs/agentic_memory_stateful.json
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_reflection/eval.jsonl --strategy reflective --report-path runs/agentic_reflection_reflective.json
```

The key question is not "can the agent talk to tools?" but "does memory or reflection improve task success enough to justify the extra steps?"

## `M00-M04`: Multimodal and Grounding

```bash
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal/eval.jsonl --strategy vision_augmented --report-path runs/multimodal_vision_augmented.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_noisy/eval.jsonl --strategy structured_pipeline --report-path runs/multimodal_noisy_structured_pipeline.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_grounding/eval.jsonl --strategy grounded_pipeline --report-path runs/multimodal_grounding_grounded_pipeline.json
```

This path is meant to teach the difference between:

- OCR text extraction
- page routing
- region grounding
- structured answer generation

## `M05`: Document Workflow Pipeline

```bash
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_workflow/eval.jsonl --strategy grounded_pipeline --report-path runs/multimodal_workflow_grounded_pipeline.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_workflow/eval.jsonl --strategy document_pipeline --report-path runs/multimodal_workflow_document_pipeline.json
python3 code/stage_harness/regression_compare.py --baseline-report runs/multimodal_workflow_grounded_pipeline.json --candidate-report runs/multimodal_workflow_document_pipeline.json --output runs/multimodal_workflow_regression_diff.json
```

This path teaches the next production step after grounding: page routing and region selection are still not enough if the answer requires cross-page joins, table normalization, and final owner lookup.

## `H11-H36`: Regression, Release, and Artifact Governance

Run the full suite:

```bash
python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md
```

Run the stricter ship gate version:

```bash
python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md \
  --strict \
  --require-ship
```

Generate artifact lifecycle views:

```bash
python3 code/stage_harness/artifact_catalog.py \
  --runs-dir runs \
  --manifest manifests/regression_v2_suite.json \
  --policy-path manifests/artifact_lifecycle_policy.json \
  --output runs/artifact_catalog.json \
  --md-output runs/artifact_catalog.md

python3 code/stage_harness/baseline_snapshot.py \
  --catalog runs/artifact_catalog.json \
  --label ship-ready-2026-04-10 \
  --output-root artifacts/baselines
```

Generate step-level and task-level replay commands:

```bash
python3 code/stage_harness/failure_replay.py \
  --suite-report runs/regression_suite_report.json \
  --output runs/failure_replay_plan.json \
  --md-output runs/failure_replay_plan.md
```

This last command is important even when the suite passes. Weak baselines still produce failed samples, and the replay plan turns them into ready-to-run `--task-id` commands under `runs/replay/`.

Generate the end-to-end notification delivery decision:

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

This command is the shortest path to answer:

- where would this run route?
- is live dispatch allowed?
- what happened when delivery was attempted?

## Recommended Reading Order for Operators

If you are treating this repo like a release-facing lab instead of a tutorial, use this order:

1. [runbook_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/runbook_en.md)
2. [ci_regression_guide_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/ci_regression_guide_en.md)
3. [tracks/harness/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tracks/harness/README.md)
4. [tasks/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/README.md)

The first document tells you what to run. The second tells you how to interpret the resulting release artifacts.
