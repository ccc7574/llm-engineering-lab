# Roadmap V2

## Positioning

`LLM Engineering Lab` V2 is no longer framed as a minimal internal AI assistant demo repo. It is an immersive model engineering lab for non-research engineers.

The reader is treated as a new engineer joining a model team in 2026. The goal is to understand, optimize, evaluate, and operationalize model behavior under realistic constraints.

## Core Goals

- explain how model capability is shaped by training, post-training, evaluation, and engineering decisions
- make learning feel close to real work instead of concept-only instruction
- let readers observe core principles through small, runnable experiments
- cover the tradeoffs faced by big AI labs, mid-size AI companies, and small teams

## Non-Goals

- reproducing frontier-scale SOTA training systems
- becoming a generic production platform replacement
- spreading across every popular trend
- confusing prompt tweaking with model engineering mastery

## Design Principles

### 1. Task-Driven Immersion

Every module is structured as a realistic work order rather than a textbook chapter.

Each task should include:

1. background
2. task goal
3. business and resource constraints
4. code entry points
5. experiment steps
6. metrics and acceptance criteria
7. production risks
8. retrospective and extensions

### 2. Progressive Depth

Each track has three layers:

- `Starter`
- `Practitioner`
- `Production-minded`

### 3. Eval First

Define the task, samples, grader, and regression metrics before changing training or inference.

### 4. Harness First

Training, evaluation, inference, experiment tracking, checkpoint management, and release checks should be understood as one engineering system.

### 5. Explicit Company-Scale Tradeoffs

For the same capability, the repo should make it clear how the solution differs for:

- big-tech teams
- mid-size AI companies
- small teams

### 6. Principles Must Land in Code and Experiments

Every concept should be grounded in:

- a small runnable code path
- a comparison experiment
- a set of metrics
- a realistic failure case

## Overall Structure

```text
llm-engineering-lab/
  README.md
  README_EN.md
  docs/
    project_charter.md
    project_charter_en.md
    roadmap_v2.md
    roadmap_v2_en.md
    learning_paths.md
    learning_paths_en.md
    role_learning_paths.md
    role_learning_paths_en.md
    runbook.md
    runbook_en.md
    ci_regression_guide_zh.md
    ci_regression_guide_en.md
  tracks/
  cases/
  tasks/
  code/
  eval/
  datasets/
```

## The Six Tracks

### Track P: Pretraining

Focus:

- tokenizer and data distribution
- next-token prediction mechanics
- transformer blocks and context usage
- data mixture, curriculum, domain adaptation
- context length extension
- stability and scaling intuition

Suggested tasks:

- `P00` minimal pretraining loop
- `P01` token, batch, and loss
- `P02` proving context usage
- `P03` transformer block dissection
- `P10` data mixture and sampling strategy
- `P11` continued pretraining / domain adaptation
- `P12` context length extension
- `P20` stability and failure review

### Track S: Post-Training

Focus:

- prompt protocols and supervision design
- reasoning traces
- verifier / reranker
- rejection sampling
- preference optimization
- behavior, style, refusal, and stability shaping

Suggested tasks:

- `S00`
- `S01`
- `S02`
- `S10`
- `S11`
- `S12`
- `S20`
- `S21`
- `S22`

### Track C: Coding

Focus:

- code completion and infill
- repo context construction
- bug fixing
- unit test generation
- execution feedback
- self-repair
- code benchmark design

Suggested tasks:

- `C00`
- `C01`
- `C02`
- `C03`
- `C10`
- `C11`
- `C12`
- `C13`
- `C20`
- `C21`

### Track M: Multimodal

Focus:

- image-text input formatting
- OCR vs document understanding
- chart and table reasoning
- visual grounding
- multimodal SFT
- multimodal evaluation

Suggested tasks:

- `M00`
- `M01`
- `M02`
- `M10`
- `M11`

### Track A: Agentic

Focus:

- tool use and function calling
- planner-executor patterns
- memory and state
- reflection
- recovery
- approval and permission boundaries
- browser / code / office workflows

Suggested tasks:

- `A00`
- `A01`
- `A02`
- `A10`
- `A11`
- `A20`

### Track H: Harness

Focus:

- dataset registry
- run config
- experiment tracking
- checkpoint registry
- eval runner
- latency, throughput, and cost
- regression gates
- release criteria

Suggested tasks:

- `H00`
- `H01`
- `H02`
- `H03`
- `H10`
- `H20`

## Learning Layers

### Layer 1: Core Intuition

For engineers who are new to model engineering.

Suggested coverage:

- `P00-P03`
- `S00-S02`
- `H00`

### Layer 2: Capability Optimization

For engineers who already ran the minimum loop and want to understand targeted capability gains.

Suggested coverage:

- `P10-P12`
- `S10-S12`
- `C00-C03`
- `M00-M02`
- `A00-A02`
- `H01-H03`

### Layer 3: Production-Minded Engineering

For engineers who need to fit models into real team workflows.

Suggested coverage:

- `P20`
- `S20-S22`
- `C10-C21`
- `M10-M11`
- `A10-A20`
- `H10-H20`

## Company Layers

### `bigtech`

- strong platformization and governance
- large-scale eval and release criteria
- stricter safety, rollback, and regression discipline

### `mid_company`

- open-model adaptation with tighter cost/quality pressure
- domain-specific post-training and product speed
- sharper quality / latency / cost tradeoffs

### `small_team`

- API-first or lightweight fine-tuning
- faster iteration and lower-cost experimentation
- stronger dependence on workflow design and harness discipline

## 2026-Oriented Evaluation Requirements

V2 should not reduce evaluation to one top-line accuracy number. It should expose:

- capability metrics: loss, exact match, format success, `pass@k`, task success rate
- process metrics: sampled candidates, tool calls, step count, verifier calls
- engineering metrics: latency, throughput, token cost, GPU hours, memory use
- reliability metrics: regression rate, failure distribution, schema violations, recovery rate

## Recommended Execution Order

The current priority is:

1. keep the bilingual entry docs and role paths consistent with the runnable repo state
2. keep strengthening the harness around artifact governance and replayability
3. keep adding higher-fidelity visuals and production-style failure reviews
