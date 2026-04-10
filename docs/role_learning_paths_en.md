# Role Learning Paths

This file reorganizes `LLM Engineering Lab` into practical 2 / 4 / 6-week plans by engineering role.

If [learning_paths_en.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/learning_paths_en.md) answers "how do I progress by capability depth?", this file answers "what should I prioritize for my actual job?"

## How To Use This File

- `2 weeks`: build shared vocabulary and run the smallest loop
- `4 weeks`: reach the most common optimization and evaluation work for your role
- `6 weeks`: move into production-minded decisions, regression discipline, and release standards

## Path 1: Backend Engineer

Best for:

- engineers integrating models into services, workflows, or internal tooling
- people most sensitive to API behavior, reliability, and integration cost

2-week goals:

- understand the minimal model engineering loop
- see why prompt tuning alone is not enough
- explain the value of execution feedback, tool use, and regression gates

Suggested order:

1. `P00-P03`
2. `S00-S02`
3. `C00-C03`
4. `A00-A02`
5. `H00-H03`

4-week goals:

- handle practical coding-, agent-, and integration-related optimizations
- understand why repo context, bugfixing, reflection, and routing policies affect product stability

Suggested order:

1. `C10-C13`
2. `C20-C21`
3. `A10-A11`
4. `H10-H15`

6-week goals:

- contribute to rollout standards
- work with model teams on failure attribution, rollback rules, PR gates, and cost limits

Common mistakes:

- watching API success rate but not model regressions
- focusing only on latency and ignoring recovery behavior
- treating "integrated" as "ready for stable delivery"

## Path 2: Platform / Infra Engineer

Best for:

- engineers responsible for training/eval/release infrastructure, regression suites, or notification chains
- teams that need common entry points and delivery standards across model tasks

2-week goals:

- understand the overall flow across training, evaluation, run registry, and summary board
- understand why harness quality becomes a limiting factor for teams

Suggested order:

1. `P00-P03`
2. `S00-S02`
3. `H00-H03`

4-week goals:

- maintain regression suites, gates, artifacts, and routing policies
- place coding, agentic, and multimodal eval into one release chain

Suggested order:

1. `C10-C21`
2. `A10-A11`
3. `M03-M04`
4. `H10-H33`

6-week goals:

- unify baseline governance, route policy, dispatch policy, security boundaries, and release notes
- support big-tech-style platform standards

Common mistakes:

- building runners without reviewable artifacts
- building CI pass/fail without failure taxonomy
- tracking only top-line metrics and ignoring process or cost signals

## Path 3: Application / Product Engineer

Best for:

- engineers turning model capabilities into product value quickly
- teams constantly trading off quality, UX, latency, and cost

2-week goals:

- understand the immediate product value of instruction tuning, structured output, and tool use
- run one full loop from capability to workflow to evaluation

Suggested order:

1. `S00-S02`
2. `A00-A02`
3. `M00-M02`
4. `H00-H03`

4-week goals:

- map reflection, multimodal grounding, and coding triage to real product scenarios
- decide when a capability is worth further investment

Suggested order:

1. `S10-S12`
2. `A10-A11`
3. `M03-M04`
4. `C20-C21`

6-week goals:

- choose routes under mid-size-company or small-team constraints
- explain when to invest in post-training versus workflow versus harness

Common mistakes:

- treating a feature demo as a production-ready capability
- reading only top-line success rate instead of failure samples
- failing to distinguish model, workflow, and evaluation improvements

## Path 4: MLE / Model Platform Engineer

Best for:

- engineers who need to connect training, post-training, evaluation, and release
- people working across research, platform, and product teams

2-week goals:

- run the minimal path from pretraining to post-training
- build one mental model across eval, verifier, alignment, and harness

Suggested order:

1. `P00-P12`
2. `S00-S12`
3. `H00-H03`

4-week goals:

- run targeted optimization across post-training, coding, multimodal, and agentic tracks
- explain where gains come from and what extra cost was introduced

Suggested order:

1. `S20-S22`
2. `C10-C21`
3. `M03-M04`
4. `A10-A11`

6-week goals:

- lead a production-minded route from training to release
- choose different technical combinations for big-tech, mid-size, and small-team settings

Common mistakes:

- focusing on training loss while ignoring delivery metrics
- looking only at benchmarks and ignoring regression and release flows
- assuming a research improvement is automatically the best team investment

## Quick Route Selection

- if you care most about service reliability and integration, start with `Backend Engineer`
- if you care most about regression, release, routing, and governance, start with `Platform / Infra Engineer`
- if you care most about productization and workflows, start with `Application / Product Engineer`
- if you care most about training, eval, and end-to-end technical route design, start with `MLE / Model Platform Engineer`

## Minimum Completion Standard

After finishing any one path, you should be able to:

- explain why the 5-8 most relevant tasks matter for your role
- run the corresponding starter path independently
- interpret 2-3 core metrics and 2-3 common failure modes
- map at least one company case to your own team constraints
