# Figures

这里存放项目中的图解素材说明。

当前仓库同时保留两类素材:

- 轻量草图: Mermaid / Markdown，适合快速表达结构
- 交付级图: SVG，适合放到 README、任务文档和导出 PNG

新增交付级图:

- [harness_artifact_governance.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/harness_artifact_governance.svg)
- [coding_eval_ladder.svg](/Volumes/ExtaData/newcode/llm-engineering-lab/assets/figures/coding_eval_ladder.svg)

## 预训练闭环

```mermaid
flowchart LR
    A[Raw Text] --> B[Tokenizer]
    B --> C[Token IDs]
    C --> D[Batch Sampler]
    D --> E[GPT Model]
    E --> F[Next Token Logits]
    F --> G[Cross Entropy Loss]
    G --> H[Optimizer Step]
```

## Transformer Block

```mermaid
flowchart LR
    X[Input States] --> LN1[LayerNorm]
    LN1 --> ATT[Self Attention]
    ATT --> ADD1[Residual Add]
    ADD1 --> LN2[LayerNorm]
    LN2 --> MLP[MLP]
    MLP --> ADD2[Residual Add]
    ADD2 --> Y[Output States]
```

## 推理增强链路

```mermaid
flowchart LR
    P[Prompt] --> G[Generator]
    G --> C1[Candidate 1]
    G --> C2[Candidate 2]
    G --> C3[Candidate N]
    C1 --> V[Verifier / Vote]
    C2 --> V
    C3 --> V
    V --> A[Final Answer]
```
