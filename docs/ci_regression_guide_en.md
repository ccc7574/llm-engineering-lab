# CI and Regression Guide

This document explains how the current V2 regression suite works, how to run it locally, and how to interpret its release-facing artifacts.

## What Exists Today

The repo already has a full minimum release chain:

1. `eval/*` produces per-track reports
2. `regression_compare.py` turns baseline vs candidate into diffs
3. `summary_board.py` aggregates the cross-track view
4. `gate_check.py` emits `ship / hold / block`
5. `suite_runner.py` executes the full manifest in one deterministic sequence
6. GitHub Actions runs the same suite on PRs, `main`, manual dispatches, and schedules

This means the project is no longer just a bag of runnable demos. It has a real regression and release discipline.

The multimodal ladder now spans four layers:

- text-only vs vision-augmented
- noisy OCR vs structured extraction
- grounding vs page/region-aware parsing
- grounded parsing vs document workflow joins

The agentic ladder now spans four layers as well:

- direct answer vs tool use
- tool use vs stateful recovery
- tool use vs reflective repair
- stateful execution vs planner/observer governance

The post-training ladder now includes release-facing preference checks:

- base checkpoint vs DPO aligned checkpoint
- base checkpoint vs GRPO-like aligned checkpoint
- chosen win rate / preference margin gains
- drift to reference via a KL-style proxy

## Core Files

- suite runner: `code/stage_harness/suite_runner.py`
- suite manifest: `manifests/regression_v2_suite.json`
- workflow: `.github/workflows/regression-suite.yml`
- suite report:
  - `runs/regression_suite_report.json`
  - `runs/regression_suite_report.md`
- summary board:
  - `runs/summary_board.json`
  - `runs/summary_board.md`
- gate report:
  - `runs/gate_report.json`
- artifact governance:
  - `runs/artifact_catalog.json`
  - `runs/artifact_catalog.md`
  - `runs/failure_replay_plan.json`
  - `runs/failure_replay_plan.md`
- delivery orchestration:
  - `runs/notification_delivery.json`
  - `runs/notification_delivery.md`
- release-facing artifacts:
  - `runs/release_note.json`
  - `runs/release_note.md`
  - `runs/notification_digest.json`
  - `runs/notification_digest.md`
  - `runs/harness_trend_board.json`
  - `runs/harness_trend_board.md`

## Local Run Modes

### 1. Full Local Regression

```bash
python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md
```

Use this when:

- you changed multiple tracks
- you added a new task or metric
- you want the full artifact set

### 2. CI-Like Ship Gate

```bash
python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md \
  --strict \
  --require-ship
```

Use this when:

- you want the process to fail on any broken step
- you want local behavior to match the release gate
- you want to test whether the repo is ship-ready right now

### 3. Changed-Scope Run

```bash
git diff --name-only HEAD^ HEAD > runs/changed_files.txt

python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --changed-files-path runs/changed_files.txt \
  --clean-regression-artifacts \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md \
  --strict
```

Use this when:

- the PR is concentrated in one track
- you want faster feedback before running the full suite
- you want to avoid stale diff artifacts polluting the current run

## What the Workflow Does

The GitHub workflow:

1. checks out the repo
2. sets up Python
3. runs the suite
4. requires the suite to pass
5. requires the release gate to be `ship`
6. uploads JSON and Markdown artifacts
7. builds trend, digest, and release-note artifacts
8. prepares optional notification routing and dispatch inputs

On `pull_request`, the workflow tries to use changed-scope mode first.

If the changed files touch `harness` paths, it upgrades to the full suite automatically.

## How to Read the Outputs

### `runs/regression_suite_report.md`

Start here when you need the full execution trace:

- which steps ran
- duration and return code
- expected outputs
- failure category and failure summary when something breaks

### `runs/summary_board.md`

Use this for the cross-track board:

- baseline vs candidate deltas
- gate threshold status
- per-track regression rows

### `runs/gate_report.json`

Use this when you need the final decision:

- `ship`
- `hold`
- `block`

### `runs/artifact_catalog.md`

Use this to decide what each run artifact means:

- `promote_on_ship`
- `retain_for_replay`
- `ephemeral_debug`

This is the artifact that tells operators which files are release evidence and which are only for debugging or replay.

### `runs/failure_replay_plan.md`

Use this when you need the next action, not just the diagnosis:

- failed suite-step replay commands
- failed task/sample replay commands
- generated `--task-id` commands with dedicated `runs/replay/*.json` outputs

This is useful even when the suite passes, because weak baseline reports still expose failed samples that are worth replaying and teaching from.

### `runs/notification_delivery.md`

Use this when you want the end-to-end notification answer in one place:

- which channel route selection chose
- whether dispatch policy allowed live sending
- whether dispatch was actually attempted
- why delivery was skipped or failed

This is the artifact that turns route, policy, and dispatch from separate debugging steps into one operator-facing decision trail.

### `runs/release_note.md`

Use this for release owner communication:

- track status
- gate result
- slowest steps
- cost and drift summary

### `runs/harness_trend_board.md`

Use this for release operations and recurring regression reviews:

- duration hotspots
- cost drift
- snapshot-to-snapshot change

## What This Teaches Engineers

The harness layer exists to teach a production truth:

- model quality is not only about training
- release confidence depends on evaluation discipline
- failed samples must be replayable
- artifact retention must be intentional
- company scale changes how much process is worth paying for

That is why the lab treats training, eval, regression, gating, and release artifacts as one system instead of separate topics.
