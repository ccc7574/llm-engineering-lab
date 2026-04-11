# M10: 用可解释 route policy 做最小多模态 SFT

## 背景

真实团队里的多模态 instruction tuning，很多时候第一步并不是直接训练一个更大的 vision backbone，而是先把“任务该走哪条专家链路”学对。

在文档理解场景里，常见失败不是模型完全看不见图像，而是:

- 该走 `vision_augmented` 的单页读图任务，被错误送进了重型文档链路
- 该走 `grounded_pipeline` 的多页 routing / region grounding 任务，被当成普通 OCR
- 该走 `document_pipeline` 的跨页 join 工作流，被过早截停在 grounding 层

如果团队没有一个可训练、可回归、可解释的 route policy，就很难把 multimodal SFT 做成真正可交付的工程能力。

参考图:

- [multimodal_sft_router.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/multimodal_sft_router.svg)

## 任务目标

- 增加一个最小可训练的多模态 route-policy SFT 路径
- 用监督标签学习在四类专家策略之间路由:
  - `vision_augmented`
  - `structured_pipeline`
  - `grounded_pipeline`
  - `document_pipeline`
- 建立 `heuristic_router` 对 `learned_router` 的统一回归对照
- 把该路线接进 regression suite、summary board 和中英文 runbook

## 业务与资源约束

- 不伪装成“大模型视觉微调”
- 不引入新的重型视觉依赖
- 训练必须在 CPU 上几秒内可跑完
- 输出必须保留 route accuracy、task success rate 和步骤/视觉 token 成本

## 代码改造点

- `code/stage_multimodal/router_sft.py`
  - 任务特征提取
  - 启发式路由基线
  - 线性 route policy 推理
- `code/stage_multimodal/train_multimodal_sft.py`
  - 最小 supervised route-policy 训练
- `eval/multimodal_sft_eval.py`
  - `heuristic_router` vs `learned_router` 对照评测
- `datasets/tiny_multimodal_sft/`
  - 训练集
  - 带 `target_strategy` 的评测集

## 交付标准

- 训练脚本能产出 route-policy checkpoint
- `heuristic_router` 在 workflow 级任务上出现可解释误路由
- `learned_router` 在评测集上的 route accuracy 和 task success rate 都优于 heuristic baseline
- regression suite 新增一组 `multimodal_sft_*` 步骤
- summary board 出现独立 `Multimodal SFT Router` 行

## 原理补充

这里的 “SFT” 指的是对 route policy 做监督学习，而不是对视觉主干做端到端微调。

这样设计有三个好处:

1. 非算法工程师能直接看到 supervision target 是什么。
2. 路由失败和任务失败的因果关系更容易解释。
3. 这更接近很多真实团队在 2026 年会先做的事情: 先把多专家链路的调度学稳，再决定是否值得投入更昂贵的视觉后训练。

## 实验步骤

```bash
python3 code/stage_multimodal/train_multimodal_sft.py \
  --data-path datasets/tiny_multimodal_sft/train.jsonl \
  --out-dir runs/multimodal_sft_router \
  --max-iters 200 \
  --eval-interval 50 \
  --learning-rate 0.2

python3 eval/multimodal_sft_eval.py \
  --data-path datasets/tiny_multimodal_sft/eval.jsonl \
  --strategy heuristic_router \
  --report-path runs/multimodal_sft_heuristic_router.json

python3 eval/multimodal_sft_eval.py \
  --data-path datasets/tiny_multimodal_sft/eval.jsonl \
  --strategy learned_router \
  --checkpoint runs/multimodal_sft_router/router.pt \
  --report-path runs/multimodal_sft_learned_router.json

python3 code/stage_harness/regression_compare.py \
  --baseline-report runs/multimodal_sft_heuristic_router.json \
  --candidate-report runs/multimodal_sft_learned_router.json \
  --output runs/multimodal_sft_regression_diff.json
```

## 结果解读

- 如果 `route_accuracy` 提升但 `task_success_rate` 没提升，说明路由标签和真实 downstream 成功条件还没完全对齐。
- 如果 `task_success_rate` 提升但 `avg_observation_steps`、`avg_reasoning_steps` 明显升高，需要评估这条路径是否值得线上成本。
- 如果 heuristic baseline 只错在 `document_pipeline` 类任务，说明 workflow join 是当前多模态系统的主要真实短板。

## 线上风险

- route policy 可能学到 task-id 或 wording shortcut，而不是真的学到任务结构
- 新增专家链路后，成本侧指标可能比纯质量指标更早成为瓶颈
- 如果标签体系定义得太粗，训练出来的 router 可能“路由正确但答案仍错”

## 复盘与延伸

- 下一步可以把 route policy 输入从结构特征扩展到更真实的 OCR / layout encoder 输出
- 可以增加 `M11` failure pack，把误路由样本做成专门的 regression bucket
- 也可以把 route confidence 接进 harness gate，模拟线上低置信度 fallback
