# C10: 给 coding 补 judge / verifier，理解“生成完了还不够”

## 背景

真实团队里，代码模型不只负责生成候选，还经常需要:

- 判断哪个候选更可信
- 在多个 patch 之间做 rerank
- 把执行结果和 issue 约束合起来做决策

## 任务目标

- 建立最小 code judge / verifier 路线
- 对比 `first_candidate` 和 `judge_rerank`
- 让读者理解 execution signal 为什么适合作为 judge 输入

## 交付标准

- 至少有一组 bugfix 候选池
- 至少有一个 rerank 评分逻辑
- 至少输出候选数、最终通过率和 judge 代价
