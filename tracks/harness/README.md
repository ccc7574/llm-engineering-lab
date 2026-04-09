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

建议首批任务:

- `H00` 统一训练与评测入口
- `H01` checkpoint 与 config 管理
- `H02` regression harness
- `H03` latency / cost profiling
