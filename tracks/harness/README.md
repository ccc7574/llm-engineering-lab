# Track H: Harness

这个能力线负责解释为什么很多团队最终是被 harness 能力限制，而不是被模型结构本身限制。

重点问题:

- 为什么要先有统一训练与评测入口
- checkpoint、config、dataset registry 为什么重要
- regression、latency、token cost 为什么必须进入日常决策

当前状态:

- V2 规划已建立
- 已有 `report_runs.py` 和 `regression_compare.py`
- 已能扫描 `runs/` 并对比基线与候选报告
- 已能对 `coding`、`repo context`、`bugfix`、`agentic`、`multimodal` 报告做最小回归比较
- 已有 `summary_board.py` 可聚合多条能力线的 regression diff、门槛状态和 Markdown 面板
- 已有 `gate_check.py` 可把 summary board 转成 `ship / hold / block` 决策
- 已有 `suite_runner.py` 与 suite manifest，可一键执行 V2 regression suite
- 已有 GitHub Actions CI launcher，可在 PR / main / schedule 中执行 suite
- 已支持 changed-scope suite 与 step retry，可把 PR 回归压缩到受影响能力线
- 已支持 notification digest，可直接输出值班/发布摘要
- 已支持 Slack / 飞书 payload artifact，可直接作为后续外发输入
- 已支持 dispatch 脚本，可用 webhook 或 dry-run 发送 payload
- 已支持 routing policy，可按 event / severity 自动选择通知通道
- 已支持 route override 与更细的 failure taxonomy，可进一步细化通知决策
- 已支持 route matrix，可把 policy 行为导出成可审阅 artifact
- 已支持 route diff，可比较 baseline 和 candidate policy 的行为变化
- 已支持 route lint 和 policy gate，可自动守住通知策略边界
- 已把 notification policy gate 接进 workflow，可在 CI 中强制执行
- 已支持 dispatch policy，可区分“已路由”和“允许真实外发”
- 已支持 review summary，可把 release / route / dispatch 三层结论压缩给 reviewer
- 已支持 latency / cost trend board，可沉淀当前 snapshot 并比较 step duration / cost drift

建议首批任务:

- `H00` 统一训练与评测入口
- `H01` checkpoint 与 config 管理
- `H02` regression harness
- `H03` latency / cost profiling
- `H11` manifest-driven regression suite
- `H12` CI launcher
- `H13` changed-scope and flaky retry
- `H14` notification digest
- `H15` external notification adapter
- `H16` notification dispatch
- `H17` notification routing policy
- `H18` route override and taxonomy
- `H19` notification route matrix
- `H21` notification policy regression
- `H22` notification policy gate
- `H23` workflow policy gate
- `H24` notification dispatch policy
- `H25` notification review summary
- `H26` latency / cost trend board
