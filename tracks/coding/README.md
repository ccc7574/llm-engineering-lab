# Track C: Coding

这个能力线负责解释代码模型为什么特殊，以及如何围绕代码任务做训练、评测和优化。

重点问题:

- 代码模型的数据和自然语言模型有什么不同
- repo-level context 如何组织
- bugfix、test generation、execution feedback 如何进入模型闭环
- 为什么 coding eval 不能只看表面流畅度

当前状态:

- V2 规划已建立
- 已有 `tiny_coding` 数据、`baseline_runner.py` 和 `eval/coding_eval.py`
- 已形成最小 execution-based eval 闭环
- 已有 `tiny_repo_context` 与 `tiny_bugfix` 的 runnable 对照实验
- `tiny_repo_context` 已支持 query-aware `retrieved` context packing

建议首批任务:

- `C00` 代码补全最小基线
- `C01` repo context packing
- `C02` bugfix 微调
- `C03` execution-based eval
- `C10` coding judge / verifier
- `C11` multi-file patch protocol

当前可直接运行的最小命令见 [runbook.md](/Volumes/ExtaData/newcode/llm-engineering-lab/docs/runbook.md) 中的 `C00-C03` 段落。
