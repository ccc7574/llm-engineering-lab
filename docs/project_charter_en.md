# Project Charter

## One-Line Definition

`LLM Engineering Lab` is an immersive model engineering lab for non-research engineers. It uses realistic work orders to connect pretraining, post-training, coding, multimodal, agentic, and harness engineering into one progressive learning path.

## Why This Project Exists

Many engineers already work with models every week, but still run into the same gaps:

- they know how to call a model, but not why its behavior emerged
- they know the names `SFT`, `RAG`, or `agent`, but not what each method actually changes
- they can ship a demo, but lack evaluation, regression, cost, and risk discipline
- they struggle to connect model principles with real team decisions

This project exists to close those gaps.

## Goals

- help non-research engineers run and understand the smallest complete model engineering loop
- show how model capability is shaped by training, post-training, inference strategy, and engineering choices
- make the learning experience feel close to a 2026 model team workflow
- give engineers the language of experiments, metrics, and work orders instead of vague intuition
- provide practical routes for big-tech teams, mid-size AI companies, and small teams

## Non-Goals

- reproducing frontier-scale SOTA training systems
- becoming a general-purpose production platform
- covering every paper or every trending direction
- pretending that a working demo equals mastery of model engineering

## Intended Readers

- engineers from backend, platform, data, application, or client backgrounds
- people who can read code and reason about systems, but are not ML researchers
- practitioners who want to understand model optimization from a work perspective
- teams that want to translate model engineering methods into product scenarios

## Structure

V2 organizes the repo around six capability tracks:

- `Pretraining`
- `Post-Training`
- `Coding`
- `Multimodal`
- `Agentic`
- `Harness`

It also adds three company-context layers:

- `bigtech`
- `mid_company`
- `small_team`

## Working Method

- `Task-driven`: learning progresses through realistic tasks, not abstract chapters
- `Progressive depth`: each track has Starter, Practitioner, and Production-minded layers
- `Eval First`: define metrics and samples before changing training or inference
- `Harness First`: view training, eval, inference, tracking, and regression as one engineering system
- `Case layering`: make company-scale tradeoffs explicit instead of pretending there is one universal path

## Success Criteria

The project starts having real delivery value when:

- a new reader can finish one Starter path independently
- readers can map ideas to code, experiments, and metrics
- at least 12 tasks form a `docs + code + data + eval` loop
- readers can explain what SFT, verifier, preference optimization, tool use, and harness each solve
- the big-tech, mid-size, and small-team cases all show clear constraints and tradeoffs

## Current Phase

The repo already has a runnable base across all six tracks, including:

- `stage0_bigram`
- `stage1_nanogpt_core`
- `stage2_sft`
- `stage3_reasoning`
- `stage4_verifier`
- `stage5_toy_alignment`
- `stage_coding`
- `stage_multimodal`
- `stage_agentic`
- `stage_harness`

The current priority is not to keep expanding topics blindly. It is to turn existing starter paths into stronger golden paths, regression views, and more realistic workflows.
