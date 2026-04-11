# LLM Engineering Lab

English readers can use this file as the primary entry point. The Chinese primary entry remains [README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/README.md).

`LLM Engineering Lab` is an immersive model engineering lab for software engineers who are not algorithm researchers.

Instead of presenting isolated concepts, the repo places the reader in a 2026-style model team environment. You learn pretraining, post-training, coding, multimodal, agentic, and harness engineering by completing realistic tasks, reading small but runnable code, and interpreting regression artifacts the way a real team would.

## What This Project Is

This project is not:

- a traditional chapter-by-chapter theory tutorial
- a large-scale SOTA training framework
- an API-only prompt engineering crash course

It is closer to:

- a model engineering practice lab
- a task-driven curriculum built around realistic work orders
- a bridge between principles, experiments, metrics, and production decisions

## Intended Audience

- engineers who can code and understand systems, but are not ML researchers
- builders who want to understand why model behavior emerges, not only how to call an API
- teams that want to transfer model optimization and evaluation methods into real product work
- readers who want to compare big-tech, mid-size AI company, and small-team tradeoffs

## Six Capability Tracks

- `Pretraining`: tokenizer, data mixture, context length, stability, continued pretraining, domain adaptation
- `Post-Training`: SFT, reasoning traces, structured output, verifier, preference optimization, behavior shaping
- `Coding`: code completion, repo context, bugfixing, test generation, execution feedback, coding eval
- `Multimodal`: document understanding, chart reasoning, visual grounding, multimodal eval
- `Agentic`: tool use, planning, memory, reflection, task execution, recovery, agent eval
- `Harness`: experiment registry, regression gates, checkpoint management, latency/cost analysis, release workflows

## Learning Layers

- `Starter`: build intuition by running the smallest loop end to end
- `Practitioner`: understand the key mechanisms and run controlled comparisons
- `Production-minded`: reason about cost, risk, rollout criteria, and team constraints

## Company Context Layers

- `bigtech`: platformization, governance, safety, stronger release criteria
- `mid_company`: domain adaptation, cost/quality tradeoffs, vertical copilots
- `small_team`: API-first delivery, low-cost iteration, fast product feedback

## Recommended Entry Docs

1. [project_charter_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/project_charter_en.md)
2. [roadmap_v2_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/roadmap_v2_en.md)
3. [learning_paths_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/learning_paths_en.md)
4. [role_learning_paths_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/role_learning_paths_en.md)
5. [runbook_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/runbook_en.md)
6. [ci_regression_guide_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/ci_regression_guide_en.md)
7. [tasks/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/README.md)
8. [code/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/code/README.md)

## Current State

The repo already has runnable starter paths across all six tracks. It now also includes:

- toy DPO / GRPO-like post-training scripts plus alignment eval
- coding judge / verifier, multi-file patching, agentic coding, SWE-bench-style triage, and `pass@k` sampling eval
- multimodal grounding, multi-page document routing, and document workflow joins
- agentic reflection and planner-observer eval
- a manifest-driven regression suite, summary board, release gate, notification routing, and CI launcher
- unified notification delivery orchestration across route, dispatch policy, and live dispatch
- English runbook and CI/regression operator docs

This means the repo is already useful as a production-minded teaching base, even though some deeper layers are still being expanded.

## Quick Start

```bash
cd llm-engineering-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For runnable commands, see [runbook_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/runbook_en.md).

For the release gate, regression suite, and artifact interpretation flow, see [ci_regression_guide_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/ci_regression_guide_en.md).

For role-oriented 2/4/6-week plans, see [role_learning_paths_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/role_learning_paths_en.md).
