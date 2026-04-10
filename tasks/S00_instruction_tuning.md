# S00: 把 Base Model 变成 Instruction Model

## 背景

base model 会续写文本，但真实产品需要的是按要求回答、遵守角色和格式协议的助手。

## 任务目标

- 定义最小 instruction 数据模板
- 让模型只对 assistant 输出部分学习
- 比较 base model 与 instruction model 的差异

## 业务与资源约束

- 数据规模可以很小
- 必须能清楚解释“助手化”到底改了什么

## 代码改造点

- `code/stage2_sft/train_sft.py`
- `code/stage2_sft/dataset.py`
- `code/stage2_sft/prompt_template.py`
- `eval/sft_eval.py`

## 交付标准

- 支持统一 instruction 模板
- 支持 assistant-only loss
- 给出 base vs SFT 的对照样例

## 原理补充

SFT 不是让模型凭空变聪明，而是让它适应新的输入输出协议和行为分布。

## 实验步骤

1. 组织 instruction 数据
2. 训练最小 SFT 模型
3. 做问答和格式输出对照

## 结果解读

重点看模型是否从“续写文本”转向“按角色回答”。

## 线上风险

- label mask 配错导致模型复述用户输入
- 线上 prompt 与训练模板不一致

## 复盘与延伸

- 对应旧任务: `T10`
- 下一步进入 `S01` 和 `S02`

