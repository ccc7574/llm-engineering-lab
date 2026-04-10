# CI 与回归套件中文指南

这份文档解释当前 `llm-engineering-lab` 已经具备的最小发布前回归链，以及团队在本地、PR 和主分支上应该怎么使用它。

## 现在已经有什么

仓库当前已经形成一条完整的最小发布链:

1. `eval/*` 生成各能力线报告
2. `regression_compare.py` 生成 baseline 与 candidate 的 diff
3. `summary_board.py` 聚合所有 regression rows
4. `gate_check.py` 产出 `ship / hold / block`
5. `suite_runner.py` 用 manifest 顺序执行整条链
6. GitHub Actions workflow 在 PR / `main` / schedule 中运行同一套 suite

这意味着仓库已经不再只是“有很多可运行脚本”，而是有了最小发布前检查体系。

## 核心文件

- suite runner: `code/stage_harness/suite_runner.py`
- suite manifest: `manifests/regression_v2_suite.json`
- CI workflow: `.github/workflows/regression-suite.yml`
- suite report:
  - `runs/regression_suite_report.json`
  - `runs/regression_suite_report.md`
- artifact catalog:
  - `runs/artifact_catalog.json`
  - `runs/artifact_catalog.md`
- failure replay plan:
  - `runs/failure_replay_plan.json`
  - `runs/failure_replay_plan.md`
- notification digest:
  - `runs/notification_digest.json`
  - `runs/notification_digest.md`
- trend board:
  - `runs/harness_trend_snapshot.json`
  - `runs/harness_trend_board.json`
  - `runs/harness_trend_board.md`
- external payloads:
  - `runs/notification_slack.json`
  - `runs/notification_feishu.json`
- dispatch:
  - `code/stage_harness/notification_dispatch.py`
  - `runs/notification_dispatch_result.json`
  - `runs/notification_dispatch_state.json`
- dispatch policy:
  - `code/stage_harness/notification_dispatch_policy.py`
  - `manifests/notification_dispatch_policy.json`
- routing:
  - `code/stage_harness/notification_route.py`
  - `manifests/notification_routes.json`
  - `code/stage_harness/notification_route_matrix.py`
  - `code/stage_harness/notification_route_diff.py`
  - `code/stage_harness/notification_route_lint.py`
  - `code/stage_harness/notification_policy_gate.py`
  - `manifests/notification_policy_gate.json`
- review summary:
  - `runs/notification_review_summary.json`
  - `runs/notification_review_summary.md`
- release note:
  - `runs/release_note.json`
  - `runs/release_note.md`
- pr comment:
  - `runs/pr_comment_result.json`
  - `runs/pr_comment_result.md`
- summary board:
  - `runs/summary_board.json`
  - `runs/summary_board.md`
- gate report:
  - `runs/gate_report.json`

## 本地怎么跑

最常用的命令有三种。

### 1. 普通本地回归

```bash
python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md
```

这个模式适合:

- 日常开发后做一次完整检查
- 新增任务或指标后确认 suite 还能跑通
- 本地查看所有产物是否按预期生成

### 2. 模拟 CI 放行

```bash
python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md \
  --strict \
  --require-ship
```

这个模式适合:

- 本地预演 CI
- 确认 suite 失败时进程会直接失败
- 确认 gate 不是 `ship` 时也会直接失败

### 3. 按变更范围跑更快的 suite

```bash
git diff --name-only HEAD^ HEAD > runs/changed_files.txt

python3 code/stage_harness/suite_runner.py \
  --manifest manifests/regression_v2_suite.json \
  --changed-files-path runs/changed_files.txt \
  --clean-regression-artifacts \
  --output runs/regression_suite_report.json \
  --md-output runs/regression_suite_report.md \
  --strict
```

这个模式适合:

- PR 只改了 `coding`、`agentic` 或 `multimodal` 某一条能力线
- 希望先拿到更快反馈
- 希望避免旧的 regression diff artifact 污染当前结果

当前 `coding` scope 已覆盖:

- `coding`
- `coding_passk`
- `repo_context`
- `bugfix`
- `multifile_bugfix`
- `testgen`
- `agentic_coding`
- `swebench`

## CI 怎么运行

workflow 文件是:

```text
.github/workflows/regression-suite.yml
```

触发方式:

- `pull_request`
- `push` 到 `main`
- `workflow_dispatch`
- `schedule`

workflow 会做这些事:

1. checkout 仓库
2. setup Python 3.11
3. 执行 suite runner
4. 要求 suite 成功
5. 要求 gate 决策为 `ship`
6. 上传 `json/md` 产物为 artifact
7. 生成 harness trend board
8. 生成 notification digest
9. 生成 Slack / 飞书 payload artifact
10. 基于 routing policy 选择 channel
11. 生成 route matrix / diff / lint / policy gate
12. 基于 dispatch policy 判断是否允许真实发送
13. 生成 review summary
14. 生成 release note
15. 在 `pull_request` 下尝试回写 PR comment
16. 把 release note、trend board、review summary、digest、route diff、suite report 和 summary board 写进 GitHub Job Summary

当前 suite 还会额外生成 artifact catalog，用来回答“这次产物里哪些应该被保留成基线，哪些只适合 replay 或调试”。

如果通过 `workflow_dispatch` 显式传入:

- `notify_channel`
- `route_override_channel`
- `require_policy_gate`

并且仓库 secret 已配置，workflow 还可以继续做可选 dispatch。
但现在只有 dispatch policy 允许时，workflow 才会真的往 webhook 发送消息。

对 `pull_request`，workflow 现在会默认尝试按 changed files 跑 scoped suite。

如果变更命中了 `harness` 相关路径，则会自动升级成全量 suite。

## 怎么看结果

几个重点 artifact 如下:

### `runs/notification_review_summary.md`

看给 reviewer / release owner 的压缩结论:

- release gate
- route policy gate
- dispatch allow / deny
- active scopes
- failed steps 和 failure counts

如果团队成员不想逐个翻 route diff、policy gate 和 digest，这个文件应该是第一入口。

### `runs/release_note.md`

看给 reviewer / release owner 的统一发布说明:

- release status
- reviewer checklist
- track statuses
- slowest steps
- cost drift
- dispatch status

如果团队后续要接 PR comment bot 或 release note 自动发布，这个文件就是最直接的上游输入。

### `runs/pr_comment_result.json` / `runs/pr_comment_result.md`

看 PR comment 回写阶段发生了什么:

- create 还是 update
- 是否缺 token
- 是否因为权限问题而降级
- 最终评论 ID / URL
- GitHub API failure diagnosis 和 actionable hint

### `runs/harness_trend_board.md`

看当前 suite 的耗时热点和 cost drift 概览:

- 当前总耗时
- 最慢 step
- 各能力线 cost signal
- 如果提供 baseline snapshot，还能看到 duration drift / cost drift

这个文件适合:

- 定时回归值班
- release owner 观察“最近是不是越来越慢”
- 判断复杂度提升是否已经开始侵蚀吞吐或成本

### `runs/notification_digest.md`

看给人读的简版结论:

- headline
- severity
- 当前是否 ship-ready
- failed steps
- gate 结论

如果团队需要把 CI 结果同步到 IM、邮件或发布频道，这个文件最适合作为正文模板。

### `runs/notification_slack.json` / `runs/notification_feishu.json`

看对外发消息的最终结构化 payload。

这两个文件适合:

- webhook 发送前最后一步
- IM 机器人接入
- 发布频道消息模板固化

### `code/stage_harness/notification_dispatch.py`

看真正的发送入口。

它支持:

- `stdout`
- `slack_webhook`
- `feishu_webhook`
- `dry-run`
- retry
- idempotency key
- dispatch result artifact

现在 workflow 在真实 dispatch 时还会顺带生成:

- `runs/notification_dispatch_result.json`
- `runs/notification_dispatch_state.json`

这样值班或 release owner 可以直接看出:

- 有没有真的发出去
- 发了几次才成功
- 是否被 duplicate guard 抑制
- 是 provider rate limit、永久拒绝，还是临时网络问题

现在 dispatch result 还会带上:

- `provider`
- `ack_status`
- `failure_category`
- `security`
- `attempts[*].retryable`
- `attempts[*].next_delay_seconds`

现在 live dispatch 还会额外做:

- provider host allowlist 校验
- 非 `https` webhook 拒绝
- 飞书 secret 签名注入

### `code/stage_harness/notification_route.py`

看通知路由选择入口。

它会根据:

- GitHub event
- digest severity
- gate / ship_ready
- failure category

从 [notification_routes.json](/Volumes/ExtaData/newcode/llm-engineering-lab/manifests/notification_routes.json) 里选出最合适的 channel。

如果有临时需求，也可以通过 `override-channel` 强行覆盖 policy。

### `runs/notification_route_matrix.md`

看当前 routing policy 在不同 event / severity / gate 组合下的整体行为。

现在矩阵还会显式展示:

- `failure_category`

这个文件适合:

- policy review
- 调整通知规则后的回归检查
- 团队沟通“这套路由到底会怎么走”

### `runs/notification_route_diff.md`

看 baseline policy 和 candidate policy 的实际路由差异。

现在 diff 行键也包含 `failure_category`，所以可以看出“只有 permission_error 被升级到飞书”这类更细粒度的变更，而不是只看到一整类 severity 被改掉。

这个文件适合:

- policy 变更 review
- 判断通知范围是否发生意外扩大
- 记录“这次通知策略升级到底改变了哪几行行为”

### `runs/notification_policy_gate.json`

看当前 route diff 是否仍在允许范围内。

这个文件适合:

- CI 守门
- policy review 最终结论
- 说明“这次通知规则变化是否超出团队约定边界”

现在这条 gate 在 workflow 里分成两层:

- report mode: 始终生成 `notification_policy_gate.json`
- enforce mode: 只有 `require_policy_gate=true` 时才要求非 `ship` 直接失败

这样 PR / 手工调试时可以先拿到 artifact，再决定是否把它作为阻断条件。

现在 gate allowlist 也带上了 `failure_category`，因此路由升级可以只批准某几个 failure taxonomy，而不必放宽整个 event / severity 区间。

### `runs/notification_dispatch_policy.json`

看 route 已经选好之后，这次 run 是否允许真实外发。

这个文件适合:

- 区分 artifact 生成和 live dispatch
- 限制 schedule / manual / PR 的通知策略
- 解释为什么 workflow 这次“有 route 但没有真的发”

### `runs/regression_suite_report.md`

看整条 suite 是否跑完，哪些 step 失败，哪些产物缺失。

### `runs/summary_board.md`

看每条能力线:

- primary metric 是什么
- baseline 与 candidate 差多少
- 是否过了 quality gate
- 成本侧信号有没有明显上升

### `runs/gate_report.json`

看最终是否:

- `ship`
- `hold`
- `block`

如果团队要把这套东西继续接到自动化发布流程，这个文件通常是最直接的输入。

### `runs/artifact_catalog.md`

看当前 `runs/` 下每个 artifact 的治理归属:

- `promote_on_ship`
- `retain_for_replay`
- `ephemeral_debug`

这个文件适合:

- release owner 判断哪些文件该跟发布一起存档
- 平台同学检查 expected outputs 是否真的落盘
- 后续 baseline snapshot 决定“该拷哪些，不该拷哪些”

### `runs/failure_replay_plan.md`

看 suite 失败后最直接的重放入口:

- 哪个 step 失败了
- failure category 是什么
- replay command 是什么
- `stdout_excerpt` 里已经暴露了哪些失败样本

这个文件适合:

- 值班同学快速重放失败步骤
- reviewer 判断这次失败是否值得阻断
- 把“失败分析”变成标准化后续动作，而不是口头约定

## 当前 suite 覆盖了什么

当前 manifest 已覆盖:

- Coding Completion
- Coding Repo Context
- Coding Bugfix
- Coding Judge
- Coding Multi-File Patch
- Coding Test Generation
- Coding Agentic Repair
- Agentic
- Agentic Memory
- Agentic Reflection
- Multimodal
- Multimodal Noisy OCR
- Multimodal Grounding
- Run Registry
- Summary Board
- Gate Check
- Artifact Catalog

当前 suite 执行策略还包括:

- `changed-scoped`
- `changed-scoped-full`
- `full`
- step 级最小重试
- failure taxonomy 与 notification digest
- Slack / 飞书 payload artifact
- dry-run / webhook dispatch
- route policy artifact
- artifact catalog / lifecycle artifact
- route override
- 更细的 runtime failure taxonomy
- failure-category-aware routing
- route matrix artifact
- route diff artifact
- route lint
- policy gate
- dispatch policy
- review summary
- trend board
- release note
- PR comment writeback

## 当前还没做的部分

这套系统已经够支撑最小交付，但离真实一线团队的完整平台还有几步:

- 更精细的 changed-scope 依赖图，而不只是 scope tag
- live adapter 的签名校验、重试和幂等保护
- PR comment 的权限诊断与更完整的 GitHub API 观测

## 建议的团队使用方式

对这个仓库，推荐按下面方式使用:

1. 本地先跑 `--strict --require-ship`
2. 提 PR 后让 GitHub Actions 自动再跑一遍
3. 合并到 `main` 后保留 artifact，作为一次可复盘的发布前证据
4. 定时任务每天或每周跑一次，防止多条能力线之间出现静默回归
