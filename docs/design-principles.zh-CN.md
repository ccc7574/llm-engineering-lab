# 设计原则：从模型知识到工程闭环

这个仓库的设计目标，是帮助非算法工程师进入模型工程，而不是追求 SOTA。

## 原则一：用小数据和小模型建立直觉

仓库里很多数据集都是 tiny 级别。这是刻意的。学习阶段最重要的是能快速运行、快速改动、快速看到结果。

等你理解了 tokenizer、batch、loss、SFT、verifier、eval、harness 的关系，再迁移到更大的模型和数据。

## 原则二：每条能力线都要有闭环

只讲 pretraining 或 SFT 不够。模型工程需要闭环：

```text
data -> training / inference -> eval -> report -> regression decision
```

这也是为什么仓库同时有 `code/`、`datasets/`、`eval/`、`tasks/`、`docs/`。

## 原则三：能力线分开学，工程系统合起来看

Pretraining、Post-Training、Coding、Multimodal、Agentic、Harness 可以分开学习，但生产里它们会互相影响。

例如 coding 能力不只是训练数据问题，还和 repo context、execution feedback、pass@k、judge、harness 有关。

## 原则四：Harness 是生产化思维的入口

很多学习材料停在“模型能输出”。这个仓库希望继续往前一步：输出如何评估，回归如何拦截，发布如何判断。

所以 `Harness` 不是附属模块，而是把模型工程转成团队工程的关键。

