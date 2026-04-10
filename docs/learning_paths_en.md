# Learning Paths

This file reorganizes `LLM Engineering Lab` V2 by learning outcome.

If [roadmap_v2_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/roadmap_v2_en.md) answers "what should this project contain?", this file answers "how should a reader progress through it?"

For role-oriented 2/4/6-week plans, see [role_learning_paths_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/role_learning_paths_en.md).

## Path 1: Core Intuition

Best for:

- engineers touching model engineering systematically for the first time
- readers who want intuition before optimization depth

Goals:

- run a minimal training and evaluation loop end to end
- understand tokenization, loss, context, and SFT at a practical level
- explain why the model behaves the way it does

Suggested order:

1. `P00`
2. `P01`
3. `P02`
4. `P03`
5. `S00`
6. `S01`
7. `S02`
8. `H00`

## Path 2: Capability Optimization

Best for:

- readers who already ran the minimum loop
- engineers who want to understand capability gains and experiment design

Goals:

- understand the main knobs in pretraining and post-training
- run small comparisons around reasoning, coding, multimodal, and tool use
- read results without being fooled by surface-level improvements

Suggested order:

1. `P10`
2. `P11`
3. `P12`
4. `S10`
5. `S11`
6. `S12`
7. `C00-C03`
8. `M00-M02`
9. `A00-A02`
10. `H01-H03`

## Path 3: Production-Minded Engineering

Best for:

- engineers who need to make real model engineering decisions in a team
- readers who need to reason about rollout standards, cost, and risk

Goals:

- evaluate options by benefit, cost, and risk
- adapt the route to company scale and team constraints
- define release criteria and regression discipline

Suggested order:

1. `P20`
2. `S20-S22`
3. `C10-C21`
4. `M10-M11`
5. `A10-A20`
6. `H10-H20`

## Company-Scale Recommendations

### Big Tech

Prioritize:

- `P10-P20`
- `S20-S22`
- `C10-C21`
- `H00-H20`

### Mid-Size AI Company

Prioritize:

- `S00-S12`
- `C00-C21`
- `A00-A11`
- `H00-H10`

### Small Team

Prioritize:

- `S00-S11`
- `A00-A02`
- `H00-H03`
- `C00-C03`

## First Delivery-Ready Paths

To keep the repo teachable and runnable, the first delivery-ready paths should remain:

1. the full `Core Intuition` path
2. `Capability Optimization` for `S10-S11`
3. `Capability Optimization` for `C00-C03`
4. `Capability Optimization` for `H01-H03`

Once these are stable, the repo stops feeling like isolated runnable pieces and starts feeling like a real curriculum.
