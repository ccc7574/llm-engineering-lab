# T21: 用 Verifier 给多个候选答案做重排

## 背景

多候选采样能提高找到正确答案的概率，但同时也引入一个新问题: 多个候选里哪一个最值得相信? 如果没有重排逻辑，self-consistency 只适合少数答案可投票的问题。

## 任务目标

- 训练一个最小 verifier
- 对候选答案进行打分和重排
- 让团队理解 generator 和 scorer 的职责分离

## 业务约束

- verifier 可以比 generator 更小
- verifier 的收益必须能量化
- 不能把 demo 写成只能对单一道题有效的硬编码

## 你需要改的代码

- `code/stage4_verifier/model.py`
- `code/stage4_verifier/train_verifier.py`
- `code/stage4_verifier/rerank.py`

## 交付标准

- 给出 verifier 训练样本
- 能对候选答案打分
- 输出重排前后结果对比

