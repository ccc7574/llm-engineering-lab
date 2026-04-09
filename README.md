# LLM Engineering Lab

`LLM Engineering Lab` 是一个面向非算法工程师的沉浸式模型工程实验室。

它不再把自己定义成“最小内部 AI 助手演练仓库”，而是把读者放进一个更接近 2026 真实团队协作的学习环境里: 你需要像模型团队的新工程师一样，围绕预训练、后训练、coding、多模态、agentic、harness 六条能力线，连续完成一组真实工单，逐步理解、掌握并实践模型优化。

## 项目定位

这个项目不是:

- 一本按章节讲概念的传统教程
- 一个追求 SOTA 的大规模训练框架
- 一个只谈 prompt engineering 的应用速成仓库

这个项目更像:

- 一个模型工程学习与演练仓库
- 一个用真实研发任务串起来的课程系统
- 一个帮助工程师把原理、实验、评测和落地连起来的工作样本

## 目标读者

- 会写代码、懂系统、懂产品交付，但不是算法研究员的工程师
- 想理解模型能力为什么这样形成，而不是只会调用 API
- 想把模型优化、评测和工程化方法应用到真实工作的人
- 想理解一线 AI 大公司、中型 AI 公司、小团队在模型路线上的不同取舍的人

## 六条能力线

### `Pretraining`

聚焦 tokenizer、数据、上下文长度、训练稳定性、continued pretraining、domain adaptation。

### `Post-Training`

聚焦 SFT、reasoning trace、structured output、verifier、偏好优化、行为塑形与稳定性。

### `Coding`

聚焦代码补全、repo-level context、bugfix、测试生成、执行反馈、代码评测。

### `Multimodal`

聚焦图文输入、文档理解、图表推理、视觉 grounding、多模态后训练与评测。

### `Agentic`

聚焦 tool use、planning、memory、reflection、任务执行、失败恢复和 agent eval。

### `Harness`

聚焦训练 harness、评测 harness、checkpoint 管理、回归门槛、时延/成本分析、实验追踪。

详细路线见 [roadmap_v2.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/roadmap_v2.md)。

## 三层学习路径

- `Starter`: 跑通最小链路，建立直觉
- `Practitioner`: 理解关键机制，能做针对性优化
- `Production-minded`: 能从真实约束出发做取舍、回归和复盘

学习路径总览见 [learning_paths.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/learning_paths.md)。

## 三类公司案例层

- `bigtech`: 更强调平台化训练、评测体系、安全与治理
- `mid_company`: 更强调成本收益、垂直能力增强和业务落地速度
- `small_team`: 更强调 API、轻微调、低成本试错和快速上线

案例入口见:

- [cases/bigtech/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/cases/bigtech/README.md)
- [cases/mid_company/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/cases/mid_company/README.md)
- [cases/small_team/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/cases/small_team/README.md)

## 当前仓库状态

V2 已经具备六条能力线的 starter path，但离“真实一线团队完整体系”还有一段距离。

已经具备最小实现的部分:

- `stage0_bigram`
- `stage1_nanogpt_core`
- `stage2_sft`
- `stage3_reasoning`
- `stage4_verifier`
- `stage_coding`
- `stage_agentic`
- `stage_multimodal`
- `stage_harness`

还在继续补强的部分:

- `stage5_toy_alignment` 的可执行 DPO / GRPO 脚本
- `coding` 的更真实 repo packing、judge / verifier 与多文件修复路径
- `multimodal` 的 OCR 噪声、表格抽取和更真实文档管线
- `agentic` 的更长链路、多任务记忆、reflection 与更复杂 recovery
- `harness` 的更完整回归门槛、成本侧指标和统一发布视图

这意味着当前仓库已经可以作为六条能力线的 starter 路线底座，但仍处于“starter path 已成型，production-minded 深水区仍在扩建”的阶段。

## 快速开始

```bash
cd llm-engineering-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Starter 路径建议

```bash
python3 code/stage0_bigram/train_bigram.py --max-iters 300
python3 code/stage1_nanogpt_core/train.py --max-iters 400
python3 code/stage1_nanogpt_core/debug_batch.py --data-path datasets/tiny_shakespeare/input.txt
python3 code/stage1_nanogpt_core/visualize_attention.py --checkpoint runs/stage1_gpt/ckpt.pt --prompt "Question: Why did the deploy fail?"
python3 code/stage2_sft/train_sft.py --init-from runs/stage1_gpt/ckpt.pt --max-iters 300
python3 eval/sft_eval.py --checkpoint runs/stage2_sft/ckpt.pt --data-path datasets/tiny_sft/eval.jsonl
python3 code/stage3_reasoning/sample_reasoning.py --checkpoint runs/stage2_sft/ckpt.pt --question "A ticket spends 12 minutes in triage and 18 minutes in repair. How long is the total?" --num-samples 5
python3 code/stage4_verifier/train_verifier.py --max-iters 200 --eval-interval 50
python3 code/stage_coding/baseline_runner.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic
python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic --report-path runs/coding_eval_heuristic.json
python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy retrieved --report-path runs/repo_context_retrieved.json
python3 eval/bugfix_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy heuristic --report-path runs/bugfix_heuristic.json
python3 eval/bugfix_judge_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy judge_rerank --report-path runs/bugfix_judge_rerank.json
python3 eval/multifile_bugfix_eval.py --data-path datasets/tiny_multifile_bugfix/eval.jsonl --strategy patch_protocol --report-path runs/multifile_bugfix_patch_protocol.json
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic/eval.jsonl --strategy tool_use --report-path runs/agentic_tool_use.json
python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_memory/eval.jsonl --strategy stateful --report-path runs/agentic_memory_stateful.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal/eval.jsonl --strategy vision_augmented --report-path runs/multimodal_vision_augmented.json
python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_noisy/eval.jsonl --strategy structured_pipeline --report-path runs/multimodal_noisy_structured_pipeline.json
python3 code/stage_harness/report_runs.py --runs-dir runs --output runs/run_registry.json
python3 code/stage_harness/summary_board.py --runs-dir runs --registry-path runs/run_registry.json --output runs/summary_board.json --md-output runs/summary_board.md
```

更完整的运行命令见 [runbook.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/runbook.md)。

## 建议的阅读顺序

如果你是第一次进入仓库，建议按这个顺序看:

1. [project_charter.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/project_charter.md)
2. [roadmap_v2.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/roadmap_v2.md)
3. [learning_paths.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/learning_paths.md)
4. [tasks/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/README.md)
5. [code/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/code/README.md)
6. [datasets/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/datasets/README.md)

## 目录结构

```text
llm-engineering-lab/
  README.md
  docs/
    project_charter.md
    roadmap_v2.md
    learning_paths.md
    runbook.md
  tracks/
    pretraining/
    post_training/
    coding/
    multimodal/
    agentic/
    harness/
  cases/
    bigtech/
    mid_company/
    small_team/
  tasks/
  code/
  datasets/
  eval/
```

## 现有任务与 V2 的关系

仓库当前保留了原有 `T00-T32` 工单体系，作为 V1 到 V2 的过渡层。

映射关系:

- `T00-T03` 对应 `Track P: Pretraining`
- `T10-T32` 主要对应 `Track S: Post-Training`

具体映射见 [tasks/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/README.md)。

## 近期优先级

当前最重要的工作不是继续堆新方向，而是把仓库从“starter 可跑”继续推到“团队可用、可复盘、可回归”的 V2 基座:

1. 统一入口文档与任务编号体系
2. 给 `Pretraining` 与 `Post-Training` 补出更稳定的 golden path
3. 把 `Coding`、`Multimodal`、`Agentic` 的 starter path 扩成更真实的工作流
4. 把 `Harness` 扩成跨能力线统一回归与汇总面板

## 交付标准

这个项目的 V2 交付，不以“文件数量”衡量，而以这些条件衡量:

- 每条能力线至少有一条可学习路径
- 至少 12 个任务形成 `文档 + 代码 + 数据 + eval` 闭环
- 至少 3 个公司案例层有完整说明
- 至少 1 套统一 harness 可以支撑回归

## 相关文档

- [project_charter.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/project_charter.md)
- [roadmap_v2.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/roadmap_v2.md)
- [learning_paths.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/learning_paths.md)
- [runbook.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/runbook.md)
- [session_handoff.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/session_handoff.md)
- [tasks/README.md](/Volumes/ExtaData/newcode/llm-engineering-lab/tasks/README.md)
