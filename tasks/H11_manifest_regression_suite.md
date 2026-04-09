# H11: 把回归命令串成 manifest-driven regression suite

## 背景

当回归链路开始跨越 coding、agentic、multimodal、harness 多条能力线时，只靠手写命令清单已经不够了。

真实团队通常会继续往前走两步:

- 用 manifest 固化“这次发布到底跑哪些检查”
- 用统一 runner 产出 suite report，方便 CI 和值班同学直接判断

## 任务目标

- 建立可审阅的 regression suite manifest
- 建立顺序执行、检查产物、输出报告的 suite runner
- 让 summary board 和 gate report 变成 suite 的自然尾部，而不是单独补跑

## 交付标准

- 至少有一份可机读 suite manifest
- 至少能顺序执行多条 eval / diff / summary / gate 命令
- 至少输出 suite JSON report 和 Markdown report
- 至少在 suite report 里保留 release decision
