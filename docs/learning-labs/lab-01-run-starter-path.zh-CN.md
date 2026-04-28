# Lab 01：跑通 Starter Path

## 目标

用最短路径跑通从 pretraining 到 eval 的基础流程，建立对仓库结构的直觉。

## 步骤

```bash
cd /Volumes/ExtaData/newcode/llm-engineering-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 code/stage0_bigram/train_bigram.py --max-iters 300
python3 code/stage1_nanogpt_core/debug_batch.py --data-path datasets/tiny_shakespeare/input.txt
python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic --report-path runs/coding_eval_heuristic.json
```

## 观察点

- 数据从哪里读入
- 脚本输出了什么
- report 文件记录了哪些字段
- eval 的策略参数如何影响结果

## 思考题

- 如果改数据集，训练和 eval 哪些地方需要同步？
- 如果新增一个能力线，最少需要哪些文件？
- 为什么学习模型工程不能只看训练脚本？

