# Session Handoff

这个文档用于跨 session 持续接力当前项目工作。目标不是写长篇总结，而是让下一次进入仓库的人能在 2 分钟内知道:

- 当前在做什么
- 已经确认了哪些事实
- 下一步应该做什么
- 哪些命令、文件和决策最关键

## 使用规则

每次开始新 session 时，先更新一条 `Session Entry`:

- 记录绝对日期和时区，不使用“今天/明天”
- 写清本轮目标、已完成步骤、关键发现、下一步动作
- 记录修改过的文件和验证结果
- 如果中途中断，也要留下“停在什么位置”

推荐最小模板:

```md
## Session Entry

- Date: 2026-04-05 20:00 CST
- Goal:
- Status:
- Key findings:
- Files touched:
- Validation:
- Next step:
```

## 当前总目标

把 `llm-engineering-lab` 从“局部实现可运行的 toy lab”推进到“面向 2026 真实工作方式的模型工程实验室 V2”，优先完成入口文档、学习路径、任务体系、能力线骨架和现有实现的语义迁移。

## 当前状态摘要

- `README.md`、`project_charter.md`、`tasks/README.md`、`scenarios/roadmap.md` 已切换到 V2 叙事。
- `docs/roadmap_v2.md` 与 `docs/learning_paths.md` 已建立为新总纲。
- `tracks/` 与 `cases/` 的目录骨架和入口 README 已补齐。
- `Pretraining` 与 `Post-Training` 仍是当前最成熟的实现链。
- `Coding` 与 `Harness` 已有 starter path，可运行 execution-based eval、run registry 和 summary board。
- `Coding` 已进一步扩到 `repo context` 与 `bugfix` 两条 runnable 路线。
- `Agentic` 已有两层 runnable 路线，可比较 `direct vs tool_use` 以及 `tool_use vs stateful`。
- `Multimodal` 已有两层 runnable 路线，可比较 `text-only vs vision-augmented` 以及 `ocr_only vs structured_pipeline`。
- `Harness` 已能把 summary board 转成 `ship / hold / block` 的 gate report。
- `Coding` 已补到 test generation，可用 `bug_detection_rate` 评测测试质量。
- `Coding` 已补到 agentic coding loop，可比较 `single_pass` 与 `repair_loop`。
- `Harness` 已补到 manifest-driven regression suite，可一键执行 cross-track eval、summary 和 gate。
- `Harness` 已补到 GitHub Actions CI launcher，可在 PR / main / schedule 中执行 suite。
- 已新增中文 CI / 回归指南，便于直接交付给中文工程团队使用。
- `Harness` 已补到 changed-scope suite 和 step retry，可按变更范围压缩 PR 回归。
- `Harness` 已补到 notification digest，可把 suite/gate 结果压缩成值班摘要。
- `Harness` 已补到 Slack / 飞书 payload artifact，可作为后续 webhook / bot 外发输入。
- `Harness` 已补到 notification dispatch，可在配置 webhook 时直接发送。
- `Harness` 已补到 notification routing policy，可按 event / severity 选择 channel。
- `Harness` 已补到 route override 与更细 failure taxonomy，可支持临时人工覆盖和更细通知决策。
- `Harness` 已补到 route matrix，可把 routing policy 导出成可审阅 artifact。
- 当前仍未成体系的主要是: 更复杂的 multimodal OCR / table / grounding 联合管线、更长链路的 agentic memory / reflection，以及更深入的 cost / latency / live policy integration。

## Session Entry

- Date: 2026-04-10 04:50 CST
- Goal: 给通知策略补 route matrix，让 policy 的整体行为可以一次性审阅。
- Status: 已完成 route matrix 生成器、任务文档和中文文档更新。
- Key findings:
  - route policy 一旦跨越多个 event 和 severity 维度，只靠单 case 验证很容易漏掉行为变化。
  - route matrix 很适合作为 policy review artifact，因为它能把“规则写成了什么”和“实际会怎么路由”对应起来。
  - 当前仓库的 Harness 已经具备从单次 route 选择到全局 route matrix 的两层可视化能力。
- Files touched:
  - `code/stage_harness/notification_route_matrix.py`
  - `tasks/H19_notification_route_matrix.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/ci_regression_guide_zh.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 code/stage_harness/notification_route_matrix.py --routes manifests/notification_routes.json --output runs/notification_route_matrix.json --md-output runs/notification_route_matrix.md`
  - 结果:
    - route matrix 已生成
    - 覆盖 `event x severity x gate` 共 `36` 行
- Next step:
  - 把 Harness 往 route matrix diff、policy regression check、scheduled dispatch routing 推进
  - 或把 Multimodal 往 grounding / multi-page doc pipeline 推进

## Session Entry

- Date: 2026-04-10 04:35 CST
- Goal: 给通知链补 route override 和更细 failure taxonomy，让 routing 既自动又可人工覆盖。
- Status: 已完成 override channel、workflow 输入、failure taxonomy 细化和中文文档更新。
- Key findings:
  - 真正的一线通知链不能只有自动路由，还必须支持临时 override，否则值班场景会很僵硬。
  - failure taxonomy 细化后，后续完全可以继续往“不同 failure category 走不同 route”推进。
  - 当前仓库已经具备 `failure taxonomy -> digest -> route policy -> override -> dispatch` 的完整决策链。
- Files touched:
  - `code/stage_harness/suite_runner.py`
  - `code/stage_harness/notification_route.py`
  - `.github/workflows/regression-suite.yml`
  - `tasks/H18_route_override_and_taxonomy.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/ci_regression_guide_zh.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 code/stage_harness/notification_route.py --digest runs/notification_digest.json --routes manifests/notification_routes.json --event-name workflow_dispatch --default-channel none --override-channel feishu_webhook --output runs/notification_route.json`
  - 结果:
    - override 生效
    - route artifact 已包含 `override_applied=true`
    - failure taxonomy 新增 `missing_input`、`permission_error`、`report_parse_error`、`logic_error`
- Next step:
  - 把 Harness 往 route-by-failure-category、schedule-only dispatch、policy test matrix 推进
  - 或把 Multimodal 往 grounding / multi-page doc pipeline 推进

## Session Entry

- Date: 2026-04-10 04:20 CST
- Goal: 把通知链再推进到 routing policy，让 workflow 不再硬编码发往哪个通道。
- Status: 已完成 routing selector、route manifest、workflow 接入和中文文档更新。
- Key findings:
  - 对真实团队来说，dispatch 和 routing 是两层不同问题: 前者负责“怎么发”，后者负责“该不该发、发到哪”。
  - route manifest 把“schedule 正常报告去 Slack、异常去飞书”这类规则显式化了，后续维护成本会低很多。
  - 当前仓库的 Harness 已经具备 `digest -> payload -> route -> dispatch` 的完整通知控制链。
- Files touched:
  - `code/stage_harness/notification_route.py`
  - `manifests/notification_routes.json`
  - `.github/workflows/regression-suite.yml`
  - `tasks/H17_notification_routing_policy.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/ci_regression_guide_zh.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 code/stage_harness/notification_route.py --digest runs/notification_digest.json --routes manifests/notification_routes.json --event-name schedule --default-channel none --output runs/notification_route.json`
  - 结果:
    - 当前 healthy scheduled run 会路由到 `slack_webhook`
    - route artifact 已包含 `channel`、`reason`、`payload_path`
- Next step:
  - 把 Harness 往 route override、failure taxonomy 细分、真实外部 secret/adapter 整合推进
  - 或把 Multimodal 往 grounding / multi-page doc pipeline 推进

## Session Entry

- Date: 2026-04-10 04:05 CST
- Goal: 把通知链再推进到 dispatch 层，让 payload 可以在有 webhook 的环境里直接外发。
- Status: 已完成 dispatch 脚本、workflow 可选发送参数，以及中文文档接入。
- Key findings:
  - payload 资产标准化之后，dispatch 层可以做得非常薄，只负责通道和发送策略。
  - `stdout + dry-run + webhook` 这三层模式足够覆盖本地开发、CI 演练和真实外发三种场景。
  - 当前仓库的 Harness 已经具备 `digest -> payload -> dispatch` 的完整通知执行链。
- Files touched:
  - `code/stage_harness/notification_dispatch.py`
  - `.github/workflows/regression-suite.yml`
  - `tasks/H16_notification_dispatch.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/ci_regression_guide_zh.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 code/stage_harness/notification_dispatch.py --payload runs/notification_slack.json --channel slack_webhook --webhook-url https://example.invalid/webhook --dry-run`
  - 结果:
    - dry-run 输出成功
    - dispatch 支持 webhook 参数与环境变量两种方式
- Next step:
  - 把 Harness 往 schedule-specific routing、failure taxonomy 细化、真实外部发送适配推进
  - 或把 Multimodal 往 grounding / multi-page doc pipeline 推进

## Session Entry

- Date: 2026-04-10 03:50 CST
- Goal: 把 Harness 再推进到 external notification adapter，给 digest 生成可直接外发的 Slack / 飞书 payload。
- Status: 已完成 payload 生成器、workflow 接入和中文文档更新。
- Key findings:
  - 对真实团队来说，digest 解决了“给人看”，payload 解决了“给系统发”。
  - 先把 payload artifact 标准化，再接 webhook 或 bot token，能显著降低后续通知接入成本。
  - 当前仓库的 Harness 已经具备 `suite -> digest -> payload` 的完整通知准备链。
- Files touched:
  - `code/stage_harness/notification_payloads.py`
  - `.github/workflows/regression-suite.yml`
  - `tasks/H15_external_notification_adapter.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/ci_regression_guide_zh.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 code/stage_harness/notification_payloads.py --digest runs/notification_digest.json --slack-output runs/notification_slack.json --feishu-output runs/notification_feishu.json`
  - 结果:
    - `runs/notification_slack.json` 已生成
    - `runs/notification_feishu.json` 已生成
    - payload 已包含 headline、gate、steps、failed steps
- Next step:
  - 把 Harness 往真实 webhook adapter、scheduled digest routing、failure taxonomy 细分推进
  - 或把 Multimodal 往 grounding / multi-page doc pipeline 推进

## Session Entry

- Date: 2026-04-10 03:35 CST
- Goal: 把 Harness 再推进到 failure taxonomy 和 notification digest，让 CI 结果可以直接给人看。
- Status: 已完成 suite failure taxonomy、digest 生成器、CI summary 接入，以及中文文档更新。
- Key findings:
  - 当 suite 变长以后，“让机器能判定”只解决了一半问题，另一半是“让人一眼知道现在该不该发”。
  - `notification_digest.md` 非常适合作为后续 IM / 邮件 / 飞书通知的正文模板，因为它已经把 headline、severity、failed steps 和 gate 聚合好了。
  - 当前仓库的 Harness 已经具备 `run -> diff -> summary -> gate -> digest -> CI summary` 的完整最小闭环。
- Files touched:
  - `code/stage_harness/suite_runner.py`
  - `code/stage_harness/notification_digest.py`
  - `.github/workflows/regression-suite.yml`
  - `tasks/H14_notification_digest.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/ci_regression_guide_zh.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_harness`
  - `python3 code/stage_harness/suite_runner.py --manifest manifests/regression_v2_suite.json --output runs/regression_suite_report.json --md-output runs/regression_suite_report.md --strict --require-ship`
  - `python3 code/stage_harness/notification_digest.py --suite-report runs/regression_suite_report.json --summary-board runs/summary_board.json --gate-report runs/gate_report.json --output runs/notification_digest.json --md-output runs/notification_digest.md`
  - 结果:
    - digest 已生成
    - 当前 headline=`Regression suite passed`
    - 当前 severity=`info`
    - 当前 `ship_ready=true`
- Next step:
  - 把 Harness 往 external notification adapter、failure taxonomy 细化、scheduled digest 推进
  - 或把 Multimodal 往 grounding / multi-page doc pipeline 推进

## Session Entry

- Date: 2026-04-10 03:20 CST
- Goal: 把 Harness 再推进到 changed-scope suite 和 flaky retry，让 PR 回归更接近真实团队执行方式。
- Status: 已完成 suite step retry、changed-file scope 选择、PR changed-only CI 模式，以及对应中文文档。
- Key findings:
  - 对真实团队来说，full suite 很重要，但不是每个 PR 都应该先跑 full suite。
  - `scope tag + run_all_scopes` 这种设计足够轻量，适合当前教学仓库，也能表达“改到 harness 就升格全量回归”的真实规则。
  - suite report 里加入 `run_mode`、`active_scopes`、`attempt_count` 后，CI 结果的可解释性明显更强。
- Files touched:
  - `code/stage_harness/suite_runner.py`
  - `manifests/regression_v2_suite.json`
  - `.github/workflows/regression-suite.yml`
  - `tasks/H13_changed_scope_and_retry.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/ci_regression_guide_zh.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_harness`
  - `python3 code/stage_harness/suite_runner.py --manifest manifests/regression_v2_suite.json --strict --require-ship`
  - `python3 code/stage_harness/suite_runner.py --manifest manifests/regression_v2_suite.json --changed-file code/stage_coding/agentic_runner.py --changed-file tasks/C13_agentic_coding_loop.md --clean-regression-artifacts --output runs/regression_suite_report.json --md-output runs/regression_suite_report.md --strict`
  - 结果:
    - full suite: `passed`
    - changed-scoped suite: 仅选择 `coding + harness finalizers`
    - suite report 已包含 `run_mode`、`active_scopes`、`attempt_count`
- Next step:
  - 把 Harness 往 changed-scope 依赖图、failure taxonomy、scheduled notification 推进
  - 或把 Multimodal 往 grounding / multi-page doc pipeline 推进

## Session Entry

- Date: 2026-04-10 03:00 CST
- Goal: 把 regression suite 从“本地可跑”推进到“CI 可直接执行和放行”的状态。
- Status: 已完成 suite strict mode、require-ship gate、GitHub Actions workflow 和 CI 文档接入。
- Key findings:
  - suite runner 如果不支持严格退出码，CI 只能“跑完”，不能真正“拦住不该发的版本”。
  - 把本地 suite 和 CI suite 保持为同一个 manifest，是降低维护成本的关键。
  - 当前仓库已经具备接近真实团队的最小发布链: `manifest -> suite runner -> summary board -> gate -> CI artifact`。
- Files touched:
  - `code/stage_harness/suite_runner.py`
  - `.github/workflows/regression-suite.yml`
  - `tasks/H12_ci_launcher.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_harness`
  - `python3 code/stage_harness/suite_runner.py --manifest manifests/regression_v2_suite.json --output runs/regression_suite_report.json --md-output runs/regression_suite_report.md --strict --require-ship`
  - 结果:
    - suite `36/36 passed`
    - suite `overall_status=passed`
    - suite `release_decision=ship`
    - strict mode 本地通过，可直接映射到 CI
- Next step:
  - 把 Harness 往 flaky retry / changed-scope suite / scheduled regression 通知推进
  - 或把 Multimodal 往 grounding / page routing / multi-page doc pipeline 推进

## Session Entry

- Date: 2026-04-10 02:45 CST
- Goal: 把 Harness 再推进到 manifest-driven regression suite，让 cross-track 回归从命令清单升级到可执行 suite。
- Status: 已完成 suite manifest、suite runner、suite report artifact，以及 Harness 文档接入。
- Key findings:
  - 当回归步骤超过十几条时，真正影响团队交付效率的已经不是“有没有 eval”，而是“有没有一条稳定的发布前 suite”。
  - suite manifest 非常适合教学，因为它把“发布前要检查什么”从隐藏经验变成了显式资产。
  - 现在仓库已经具备 `eval -> regression diff -> summary board -> gate -> suite report` 的完整最小发布链。
- Files touched:
  - `code/stage_harness/suite_runner.py`
  - `manifests/regression_v2_suite.json`
  - `tasks/H11_manifest_regression_suite.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `README.md`
  - `docs/runbook.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_harness`
  - `python3 code/stage_harness/suite_runner.py --manifest manifests/regression_v2_suite.json --output runs/regression_suite_report.json --md-output runs/regression_suite_report.md`
  - 结果:
    - suite steps: `36/36 passed`
    - suite `overall_status=passed`
    - suite `release_decision=ship`
    - 新增 artifacts:
      - `runs/regression_suite_report.json`
      - `runs/regression_suite_report.md`
- Next step:
  - 把 Harness 往 CI launcher / scheduled regression / flaky retry 策略推进
  - 或把 Multimodal 往 grounding / page routing / structured extraction pipeline 推进

## Session Entry

- Date: 2026-04-10 02:30 CST
- Goal: 把 Coding 再推进到更像真实团队的 agentic coding loop，并把新路线接进 harness 与交付文档。
- Status: 已完成 tiny agentic coding 数据、repair loop runner / eval、回归产物、summary board 与 gate report 接入。
- Key findings:
  - 对非算法工程师来说，coding agent 的关键分水岭不是“能不能写出 patch”，而是“失败后会不会继续读仓库、跑测试并修第二轮”。
  - `single_pass -> repair_loop` 的对照把 repo retrieval、patch recall、test feedback、repair success 连成了一个非常清晰的教学闭环。
  - 当前 `Coding` 线已经形成 `completion -> repo context -> bugfix -> judge -> multi-file patch -> test generation -> agentic coding` 的连续工作流。
- Files touched:
  - `code/stage_coding/agentic_dataset.py`
  - `code/stage_coding/agentic_runner.py`
  - `eval/agentic_coding_eval.py`
  - `datasets/tiny_agentic_coding/eval.jsonl`
  - `tasks/C13_agentic_coding_loop.md`
  - `code/README.md`
  - `datasets/README.md`
  - `eval/README.md`
  - `tasks/README.md`
  - `tracks/coding/README.md`
  - `docs/runbook.md`
  - `README.md`
  - `code/stage_harness/summary_board.py`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_coding eval/agentic_coding_eval.py code/stage_harness`
  - `python3 eval/agentic_coding_eval.py --data-path datasets/tiny_agentic_coding/eval.jsonl --strategy single_pass --report-path runs/agentic_coding_single_pass.json`
  - `python3 eval/agentic_coding_eval.py --data-path datasets/tiny_agentic_coding/eval.jsonl --strategy repair_loop --report-path runs/agentic_coding_repair_loop.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/agentic_coding_single_pass.json --candidate-report runs/agentic_coding_repair_loop.json --output runs/agentic_coding_regression_diff.json`
  - `python3 code/stage_harness/report_runs.py --runs-dir runs --output runs/run_registry.json`
  - `python3 code/stage_harness/summary_board.py --runs-dir runs --registry-path runs/run_registry.json --output runs/summary_board.json --md-output runs/summary_board.md`
  - `python3 code/stage_harness/gate_check.py --summary-board runs/summary_board.json --output runs/gate_report.json`
  - 结果:
    - agentic coding: `0/3 -> 3/3`
    - `task_success_rate +1.000`
    - `recovery_success_rate +1.000`
    - `avg_relevant_context_recall +0.500`
    - `avg_patch_recall +0.500`
    - summary board: `11` 条 regression rows，已包含 `Coding Agentic Repair`
    - gate report: `overall_gate=ship`
- Next step:
  - 把 Harness 往 manifest-driven regression suite / CI launcher 推进
  - 或把 Coding 往 patch diff protocol / test repair / pass@k 推进

## Session Entry

- Date: 2026-04-10 02:10 CST
- Goal: 继续把 Coding 能力线推进到更接近真实工程，把 test generation 和隐藏 bug 检测接进现有 harness。
- Status: 已完成 tiny testgen 数据、test generation runner / eval、回归产物和 summary board 接入。
- Key findings:
  - test generation 的关键不在“生成了几条断言”，而在“这些断言是否能通过 reference 且抓住 hidden bug”。
  - `weak -> targeted` 的对照非常适合作为非算法工程师的第一条测试生成路线，因为 `bug_detection_rate` 比 BLEU 或断言数量更符合真实工作要求。
  - 当前 `Coding` 线已经形成 `completion -> repo context -> bugfix -> judge -> multi-file patch -> test generation` 的连续工作流。
- Files touched:
  - `code/stage_coding/testgen_dataset.py`
  - `code/stage_coding/testgen_runner.py`
  - `eval/testgen_eval.py`
  - `datasets/tiny_testgen/eval.jsonl`
  - `tasks/C12_test_generation.md`
  - `code/README.md`
  - `datasets/README.md`
  - `eval/README.md`
  - `tasks/README.md`
  - `tracks/coding/README.md`
  - `docs/runbook.md`
  - `code/stage_harness/summary_board.py`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_coding eval/testgen_eval.py code/stage_harness`
  - `python3 eval/testgen_eval.py --data-path datasets/tiny_testgen/eval.jsonl --strategy weak --report-path runs/testgen_weak.json`
  - `python3 eval/testgen_eval.py --data-path datasets/tiny_testgen/eval.jsonl --strategy targeted --report-path runs/testgen_targeted.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/testgen_weak.json --candidate-report runs/testgen_targeted.json --output runs/testgen_regression_diff.json`
  - `python3 code/stage_harness/summary_board.py --runs-dir runs --registry-path runs/run_registry.json --output runs/summary_board.json --md-output runs/summary_board.md`
  - 结果:
    - test generation: `0/3 -> 3/3`
    - `bug_detection_rate +1.000`
    - summary board: `10` 条 regression rows，已包含 `Coding Test Generation`
- Next step:
  - 把 Coding 往 agentic coding / patch diff protocol / test repair 推进
  - 或把 Harness 往 scheduled regression / CI 触发推进

## Session Entry

- Date: 2026-04-10 01:45 CST
- Goal: 把 Harness 从“会汇总回归”推进到“会做发布门槛判断”，并把本地仓库初始化后推到 GitHub。
- Status: 已完成 Git 初始化、本地首次提交、远程仓库创建与 push，以及 `gate_check.py` 发布门槛脚本。
- Key findings:
  - 对真实团队来说，summary board 只有在能变成 `ship / hold / block` 决策时才真正进入发布流程。
  - 当前仓库现在已经不只是教学文件集合，而是已经有了公开远程仓库和可机读 gate report，交付感明显提升。
  - `runs/gate_report.json` 很适合作为后续 CI / scheduled regression 的最小输入。
- Files touched:
  - `code/stage_harness/gate_check.py`
  - `tasks/H10_release_gate.md`
  - `code/README.md`
  - `tasks/README.md`
  - `tracks/harness/README.md`
  - `docs/runbook.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_harness code/stage_coding eval`
  - `python3 code/stage_harness/gate_check.py --summary-board runs/summary_board.json --output runs/gate_report.json`
  - 结果:
    - `overall_gate=ship`
    - gate report 已写入 `runs/gate_report.json`
  - Git:
    - 本地仓库已初始化
    - 首次提交: `408fc7c`
    - 远程仓库: `https://github.com/ccc7574/llm-engineering-lab`
- Next step:
  - 把 Harness 往 CI / scheduled regression 触发推进
  - 或把 Coding 往 test generation / agentic coding 推进

## Session Entry

- Date: 2026-04-10 01:35 CST
- Goal: 把 Coding 再推进一层，补齐 multi-file patch protocol，让仓库能表达“跨文件修复”和 patch recall。
- Status: 已完成 multi-file bugfix 数据、patch runner、patch eval，以及新的 regression 产物接入 summary board。
- Key findings:
  - 单文件修复和真实代码修复之间有一条很明显的分水岭: helper 修了，调用方可能还没修；调用方修了，helper 可能还是错的。
  - `single_file -> patch_protocol` 的对照对非算法工程师很有教学价值，因为它把“修复质量”显式拆成 `pass@1`、`touched_files_count`、`patch_recall` 三个信号。
  - 当前 `Coding` 线已经具备了 completion、repo context、single-file bugfix、judge rerank、multi-file patch 五种 starter path，对一线团队常见工作流已经比较接近。
- Files touched:
  - `code/stage_coding/multifile_bugfix_dataset.py`
  - `code/stage_coding/patch_runner.py`
  - `code/stage_coding/execution.py`
  - `eval/multifile_bugfix_eval.py`
  - `datasets/tiny_multifile_bugfix/eval.jsonl`
  - `tasks/C11_multi_file_bugfix_protocol.md`
  - `code/README.md`
  - `datasets/README.md`
  - `eval/README.md`
  - `tasks/README.md`
  - `tracks/coding/README.md`
  - `docs/runbook.md`
  - `README.md`
  - `code/stage_harness/summary_board.py`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_coding eval/multifile_bugfix_eval.py`
  - `python3 eval/multifile_bugfix_eval.py --data-path datasets/tiny_multifile_bugfix/eval.jsonl --strategy single_file --report-path runs/multifile_bugfix_single_file.json`
  - `python3 eval/multifile_bugfix_eval.py --data-path datasets/tiny_multifile_bugfix/eval.jsonl --strategy patch_protocol --report-path runs/multifile_bugfix_patch_protocol.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/multifile_bugfix_single_file.json --candidate-report runs/multifile_bugfix_patch_protocol.json --output runs/multifile_bugfix_regression_diff.json`
  - `python3 code/stage_harness/summary_board.py --runs-dir runs --registry-path runs/run_registry.json --output runs/summary_board.json --md-output runs/summary_board.md`
  - 结果:
    - multi-file bugfix: `0/3 -> 3/3`
    - `avg_patch_recall +0.500`
    - summary board: `9` 条 regression rows，已包含 `Coding Multi-File Patch`
- Next step:
  - 把 Coding 往 test generation / patch diff protocol / agentic coding 推进
  - 或把 Agentic 往 reflection / browser-office workflow 推进

## Session Entry

- Date: 2026-04-10 01:20 CST
- Goal: 把 Coding 从静态上下文和单候选修复推进到 query-aware repo context packing 与最小 code judge / rerank。
- Status: 已完成 `retrieved` repo context packing、上下文召回指标、coding judge / rerank 路线，以及新的 regression 产物接入 summary board。
- Key findings:
  - 对非算法工程师来说，repo context 最重要的不是“塞更多文件”，而是“有没有把关键文件召回进来”。
  - `retrieved` 路线把 `avg_relevant_context_recall` 做到 `1.00`，同时把 `pass@1` 从 `0.00` 提到 `1.00`，很适合解释上下文工程为什么是 code model 的核心能力。
  - `first_candidate -> judge_rerank` 也形成了很清晰的教学闭环: 不是所有提升都来自更强生成器，很多时候是候选打分和 rerank 机制在发挥作用。
- Files touched:
  - `code/stage_coding/context_builder.py`
  - `code/stage_coding/dataset.py`
  - `code/stage_coding/prompt_template.py`
  - `code/stage_coding/repo_context_runner.py`
  - `eval/repo_context_eval.py`
  - `datasets/tiny_repo_context/eval.jsonl`
  - `code/stage_coding/judge.py`
  - `eval/bugfix_judge_eval.py`
  - `tasks/C10_coding_judge_verifier.md`
  - `tasks/C01_repo_context_packing.md`
  - `tasks/README.md`
  - `tracks/coding/README.md`
  - `code/README.md`
  - `eval/README.md`
  - `docs/runbook.md`
  - `README.md`
  - `code/stage_harness/summary_board.py`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_coding eval/repo_context_eval.py`
  - `python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy local_only --report-path runs/repo_context_local_only.json`
  - `python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy retrieved --report-path runs/repo_context_retrieved.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/repo_context_local_only.json --candidate-report runs/repo_context_retrieved.json --output runs/repo_context_regression_diff.json`
  - `python3 -m compileall code/stage_coding eval/bugfix_judge_eval.py`
  - `python3 eval/bugfix_judge_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy first_candidate --report-path runs/bugfix_judge_first_candidate.json`
  - `python3 eval/bugfix_judge_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy judge_rerank --report-path runs/bugfix_judge_rerank.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/bugfix_judge_first_candidate.json --candidate-report runs/bugfix_judge_rerank.json --output runs/bugfix_judge_regression_diff.json`
  - `python3 code/stage_harness/summary_board.py --runs-dir runs --registry-path runs/run_registry.json --output runs/summary_board.json --md-output runs/summary_board.md`
  - 结果:
    - repo context: `0/3 -> 3/3`
    - `avg_relevant_context_recall +1.000`
    - coding judge: `0/3 -> 3/3`
    - summary board: `8` 条 regression rows，已包含 `Coding Judge`
- Next step:
  - 把 Coding 往 multi-file bugfix、test generation 或 patch-level edit protocol 推进
  - 或把 Agentic 往 reflection / browser-office workflow 推进

## Session Entry

- Date: 2026-04-10 01:05 CST
- Goal: 把 Multimodal 从干净样本问答推进到 noisy OCR / table extraction / structured pipeline 的工作流形态。
- Status: 已完成 noisy multimodal 数据、视觉样本、`ocr_only` 与 `structured_pipeline` 两种策略、字段匹配率评测，以及新的 regression 产物。
- Key findings:
  - 对多模态工程来说，“看见内容”与“抽对字段再做业务推理”是两层不同问题，必须拆开教。
  - `ocr_only` 在 noisy invoice / routing table / latency table 上直接掉到 `0/3`，很适合让工程师感受到 OCR 污染为什么会摧毁最终业务答案。
  - `structured_pipeline` 在相同样本上恢复到 `3/3`，并把 `avg_field_match_rate` 从 `0.00` 提到 `1.00`，这比只看最终 success 更能解释改动价值。
- Files touched:
  - `code/stage_multimodal/dataset.py`
  - `code/stage_multimodal/task_runner.py`
  - `eval/multimodal_eval.py`
  - `datasets/tiny_multimodal_noisy/eval.jsonl`
  - `assets/figures/multimodal_noisy_invoice.svg`
  - `assets/figures/multimodal_routing_table.svg`
  - `assets/figures/multimodal_latency_table.svg`
  - `tasks/M03_noisy_ocr_pipeline.md`
  - `tasks/M01_document_understanding.md`
  - `tasks/M02_chart_reasoning.md`
  - `tasks/README.md`
  - `tracks/multimodal/README.md`
  - `datasets/README.md`
  - `eval/README.md`
  - `code/README.md`
  - `docs/runbook.md`
  - `README.md`
  - `code/stage_harness/summary_board.py`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_multimodal eval/multimodal_eval.py`
  - `python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_noisy/eval.jsonl --strategy ocr_only --report-path runs/multimodal_noisy_ocr_only.json`
  - `python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal_noisy/eval.jsonl --strategy structured_pipeline --report-path runs/multimodal_noisy_structured_pipeline.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/multimodal_noisy_ocr_only.json --candidate-report runs/multimodal_noisy_structured_pipeline.json --output runs/multimodal_noisy_regression_diff.json`
  - `python3 code/stage_harness/summary_board.py --runs-dir runs --registry-path runs/run_registry.json --output runs/summary_board.json --md-output runs/summary_board.md`
  - 结果:
    - noisy multimodal: `0/3 -> 3/3`
    - `task_success_rate +1.000`
    - `avg_field_match_rate +1.000`
    - summary board: `7` 条 regression rows，已包含 `Multimodal Noisy OCR`
- Next step:
  - 把 Coding 往 repo context packing、judge/verifier、多文件 bugfix 推进
  - 或把 Multimodal 再往 grounding / region selection / page-level doc flows 推进
- 当前最合理的补齐顺序是:
  1. 稳定 `Pretraining` 与 `Post-Training` 的 golden path
  2. 补 `Coding` 与 `Harness` 的首批任务与实现
  3. 再扩 `Multimodal` 与 `Agentic`

## Session Entry

- Date: 2026-04-10 00:50 CST
- Goal: 把 Agentic 从“会调工具”推进到“有状态与恢复”，并把 Harness 升级成带门槛和 Markdown artifact 的统一面板。
- Status: 已完成 `state.py`、memory/recovery 数据与评测、summary board 门槛视图、Markdown artifact，以及入口文档状态修正。
- Key findings:
  - 对非算法工程师来说，agentic 的第一道分水岭不是 planner，而是“有没有显式状态”和“遇到非法中间状态时怎么恢复”。
  - `tool_use -> stateful` 的提升可以很直接地通过 `task_success_rate`、`state_reads`、`state_writes`、`recovery_attempts` 解释出来。
  - Harness 不应该只输出 diff JSON；把 baseline、candidate、gate、cost signal 汇到同一张 Markdown 板，读者才会感受到真实团队的评审节奏。
- Files touched:
  - `code/stage_agentic/state.py`
  - `code/stage_agentic/task_runner.py`
  - `eval/agentic_eval.py`
  - `datasets/tiny_agentic_memory/eval.jsonl`
  - `tasks/A10_failure_recovery.md`
  - `tasks/A02_state_memory.md`
  - `tasks/H02_regression_harness.md`
  - `tasks/H03_latency_cost_profiling.md`
  - `code/stage_harness/summary_board.py`
  - `README.md`
  - `docs/runbook.md`
  - `code/README.md`
  - `datasets/README.md`
  - `eval/README.md`
  - `tasks/README.md`
  - `tracks/agentic/README.md`
  - `tracks/harness/README.md`
  - `docs/project_charter.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_agentic code/stage_harness eval/agentic_eval.py`
  - `python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_memory/eval.jsonl --strategy tool_use --report-path runs/agentic_memory_tool_use.json`
  - `python3 eval/agentic_eval.py --data-path datasets/tiny_agentic_memory/eval.jsonl --strategy stateful --report-path runs/agentic_memory_stateful.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/agentic_memory_tool_use.json --candidate-report runs/agentic_memory_stateful.json --output runs/agentic_memory_regression_diff.json`
  - `python3 code/stage_harness/summary_board.py --runs-dir runs --registry-path runs/run_registry.json --output runs/summary_board.json --md-output runs/summary_board.md`
  - 结果:
    - agentic memory: `0/2 -> 2/2`
    - `task_success_rate +1.000`
    - summary board: `6` 条 regression rows，已包含 `Agentic Memory`
- Next step:
  - 把 Multimodal 往 OCR 噪声、字段抽取错误和表格理解推进
  - 或把 Coding 往 repo context packing / judge / multi-file bugfix 推进

## Session Entry

- Date: 2026-04-10 00:40 CST
- Goal: 给仓库补第一条可运行的 Multimodal starter path，并增加跨能力线的 harness summary。
- Status: 已完成多模态数据、视觉样本、multimodal eval，对照报告和 summary board 脚本。
- Key findings:
  - 多模态 starter path 的第一步不必直接依赖外部视觉模型，先把视觉任务格式、结构化观察和评测闭环讲清楚更重要。
  - `text_only vs vision_augmented` 的对照已经足以说明视觉上下文的工程价值。
  - `summary_board.py` 让 `coding`、`repo context`、`bugfix`、`agentic`、`multimodal` 不再是分散 JSON，而开始具备统一汇总视角。
- Files touched:
  - `assets/figures/multimodal_invoice.svg`
  - `assets/figures/multimodal_chart.svg`
  - `assets/figures/multimodal_status_card.svg`
  - `datasets/tiny_multimodal/eval.jsonl`
  - `code/stage_multimodal/__init__.py`
  - `code/stage_multimodal/dataset.py`
  - `code/stage_multimodal/task_runner.py`
  - `eval/multimodal_eval.py`
  - `code/stage_harness/summary_board.py`
  - `tasks/M00_visual_qa_loop.md`
  - `tasks/M01_document_understanding.md`
  - `tasks/M02_chart_reasoning.md`
  - `tasks/README.md`
  - `datasets/README.md`
  - `eval/README.md`
  - `code/README.md`
  - `tracks/multimodal/README.md`
  - `tracks/harness/README.md`
  - `docs/runbook.md`
  - `README.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_multimodal eval/multimodal_eval.py`
  - `python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal/eval.jsonl --strategy text_only --report-path runs/multimodal_text_only.json`
  - `python3 eval/multimodal_eval.py --data-path datasets/tiny_multimodal/eval.jsonl --strategy vision_augmented --report-path runs/multimodal_vision_augmented.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/multimodal_text_only.json --candidate-report runs/multimodal_vision_augmented.json --output runs/multimodal_regression_diff.json`
  - 结果:
    - multimodal: `0/3 -> 3/3`
    - `task_success_rate +1.000`
- Next step:
  - 用 `summary_board.py` 聚合所有 regression diff
  - 继续把 multimodal 往更接近真实 OCR / chart / doc understanding 管线推进
  - 或把 agentic 往 state / memory 和 recovery 方向继续扩

## Session Entry

- Date: 2026-04-10 00:30 CST
- Goal: 给仓库补第一条可运行的 Agentic starter path，并接入现有 harness。
- Status: 已完成 tiny agentic 数据、工具定义、task runner、agent eval 和回归对照产物。
- Key findings:
  - 最小 agentic 路线不需要复杂框架，先把 direct vs tool_use、单工具 vs 多步工具链、结果指标 vs 过程指标讲清楚就有价值。
  - `task success rate`、`avg_tool_calls`、`avg_steps` 三个指标足以支撑 starter path 的第一轮教学闭环。
  - 现有 `regression_compare.py` 已可直接复用到 agentic 报告，不必另起一套 harness。
- Files touched:
  - `datasets/tiny_agentic/eval.jsonl`
  - `code/stage_agentic/__init__.py`
  - `code/stage_agentic/dataset.py`
  - `code/stage_agentic/tools.py`
  - `code/stage_agentic/task_runner.py`
  - `eval/agentic_eval.py`
  - `tasks/A00_single_tool_loop.md`
  - `tasks/A01_multi_step_tools.md`
  - `tasks/A02_state_memory.md`
  - `tasks/README.md`
  - `datasets/README.md`
  - `eval/README.md`
  - `code/README.md`
  - `tracks/agentic/README.md`
  - `docs/runbook.md`
  - `README.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_agentic eval/agentic_eval.py`
  - `python3 eval/agentic_eval.py --data-path datasets/tiny_agentic/eval.jsonl --strategy direct --report-path runs/agentic_direct.json`
  - `python3 eval/agentic_eval.py --data-path datasets/tiny_agentic/eval.jsonl --strategy tool_use --report-path runs/agentic_tool_use.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/agentic_direct.json --candidate-report runs/agentic_tool_use.json --output runs/agentic_regression_diff.json`
  - 结果:
    - direct: `0/3`
    - tool_use: `3/3`
    - `task_success_rate +1.000`
- Next step:
  - 把 Agentic 继续推进到更明确的 state / memory 结构，而不是只保留 trace
  - 补第一条 `Multimodal` starter path
  - 或者继续提升 Harness，把多类报告统一聚合成一个 dashboard

## Session Entry

- Date: 2026-04-10 00:20 CST
- Goal: 把 Coding starter path 从单文件补全扩展到 `repo context` 和 `bugfix` 两条更真实的 runnable 路线。
- Status: 已完成两条新数据路径、对应 runner / eval 脚本，以及回归比较产物。
- Key findings:
  - `repo context` 很适合用“local_only vs contextual”这种对照方式直观展示上下文构造的重要性。
  - `bugfix` 很适合用“buggy vs heuristic fix”的 execution-based 对照，能自然衔接后续 coding post-training。
  - 当前最小 harness 已足以支撑 `coding completion`、`repo context`、`bugfix` 三类报告的数值对比。
  - 这一层做通之后，Coding 能力线已经不再只是补全 demo，而开始接近真实工程任务结构。
- Files touched:
  - `code/stage_coding/dataset.py`
  - `code/stage_coding/prompt_template.py`
  - `code/stage_coding/bugfix_dataset.py`
  - `code/stage_coding/execution.py`
  - `code/stage_coding/repo_context_runner.py`
  - `code/stage_coding/bugfix_runner.py`
  - `eval/repo_context_eval.py`
  - `eval/bugfix_eval.py`
  - `datasets/tiny_repo_context/eval.jsonl`
  - `datasets/tiny_bugfix/train.jsonl`
  - `datasets/tiny_bugfix/eval.jsonl`
  - `datasets/README.md`
  - `eval/README.md`
  - `docs/runbook.md`
  - `README.md`
  - `tracks/coding/README.md`
  - `tracks/harness/README.md`
  - `code/README.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code/stage_coding eval/repo_context_eval.py eval/bugfix_eval.py`
  - `python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy local_only --report-path runs/repo_context_local_only.json`
  - `python3 eval/repo_context_eval.py --data-path datasets/tiny_repo_context/eval.jsonl --strategy contextual --report-path runs/repo_context_contextual.json`
  - `python3 eval/bugfix_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy buggy --report-path runs/bugfix_buggy.json`
  - `python3 eval/bugfix_eval.py --data-path datasets/tiny_bugfix/eval.jsonl --strategy heuristic --report-path runs/bugfix_heuristic.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/repo_context_local_only.json --candidate-report runs/repo_context_contextual.json --output runs/repo_context_regression_diff.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/bugfix_buggy.json --candidate-report runs/bugfix_heuristic.json --output runs/bugfix_regression_diff.json`
  - 结果:
    - repo context: `0/3 -> 3/3`
    - bugfix: `0/3 -> 3/3`
- Next step:
  - 给 Coding 加入更接近仓库真实结构的 `repo context packing` 逻辑，而不仅是静态 context 文件
  - 把 Harness 扩成通用 regression runner，而不只是报告差异脚本
  - 开始补 `Multimodal` 或 `Agentic` 的第一条 runnable starter path

## Session Entry

- Date: 2026-04-10 00:05 CST
- Goal: 把 `Coding` 与 `Harness` 从纯任务骨架推进到可运行的 starter path。
- Status: 已完成 tiny coding 数据、execution-based eval、run registry 和 regression compare 的最小闭环。
- Key findings:
  - 只补任务文档不够，`Coding` 和 `Harness` 至少要各有一条可以直接运行的最小链路，V2 才算真正开始成立。
  - `tiny_coding` 用纯 Python 函数与断言测试即可构建 execution-based eval，不需要先引入额外依赖。
  - `eval/coding_eval.py` 已成功形成正反对照: `weak` 策略 `pass@1=0.000`，`heuristic` 策略 `pass@1=1.000`。
  - `code/stage_harness/report_runs.py` 已能扫描现有 `runs/*/train_state.json`，`regression_compare.py` 已能直接比较两个 JSON 报告的数值指标差异。
- Files touched:
  - `datasets/tiny_coding/train.jsonl`
  - `datasets/tiny_coding/eval.jsonl`
  - `code/stage_coding/__init__.py`
  - `code/stage_coding/dataset.py`
  - `code/stage_coding/prompt_template.py`
  - `code/stage_coding/baseline_runner.py`
  - `eval/coding_eval.py`
  - `code/stage_harness/__init__.py`
  - `code/stage_harness/run_registry.py`
  - `code/stage_harness/report_runs.py`
  - `code/stage_harness/regression_compare.py`
  - `datasets/README.md`
  - `eval/README.md`
  - `docs/runbook.md`
  - `code/README.md`
  - `README.md`
  - `tracks/coding/README.md`
  - `tracks/harness/README.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m compileall code eval`
  - `python3 code/stage_coding/baseline_runner.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic`
  - `python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy weak --report-path runs/coding_eval_weak.json`
  - `python3 eval/coding_eval.py --data-path datasets/tiny_coding/eval.jsonl --strategy heuristic --report-path runs/coding_eval_heuristic.json`
  - `python3 code/stage_harness/report_runs.py --runs-dir runs --output runs/run_registry.json`
  - `python3 code/stage_harness/regression_compare.py --baseline-report runs/coding_eval_weak.json --candidate-report runs/coding_eval_heuristic.json --output runs/coding_regression_diff.json`
  - 结果:
    - `weak`: `pass@1=0.000 (0/3)`
    - `heuristic`: `pass@1=1.000 (3/3)`
    - regression diff: `pass_at_1 +1.000`
- Next step:
  - 把 `Coding` 路线继续推进到 `repo context` 和 `bugfix` 可运行版本
  - 把 `Harness` 路线继续推进到更通用的 regression runner
  - 开始补 `Multimodal` 与 `Agentic` 的 starter path

## Session Entry

- Date: 2026-04-09 23:30 CST
- Goal: 把仓库主入口与总纲从 V1 叙事切换到 V2 的模型工程实验室体系。
- Status: 已完成入口文档重写、学习路径文档、能力线目录和公司案例目录骨架。
- Key findings:
  - 用户希望项目更聚焦预训练、后训练、coding、多模态、agentic 和 harness 工程，而不是单一“内部助手”故事。
  - 当前仓库最成熟的仍是 `stage0-stage4` 这条链，因此 V2 最合理的做法不是强行重写实现，而是先完成“语义迁移 + 结构升级 + 路线清晰化”。
  - 只改 `README` 不够，必须同步改 `project_charter`、`tasks/README`、`scenarios/roadmap`、`runbook` 和 `session_handoff`，否则入口会自相矛盾。
  - 新增 `tracks/` 和 `cases/` 后，仓库终于具备“能力线 + 公司规模约束层”的导航结构。
- Files touched:
  - `README.md`
  - `docs/project_charter.md`
  - `docs/roadmap_v2.md`
  - `docs/learning_paths.md`
  - `docs/runbook.md`
  - `tasks/README.md`
  - `scenarios/roadmap.md`
  - `docs/session_handoff.md`
  - `tracks/pretraining/README.md`
  - `tracks/post_training/README.md`
  - `tracks/coding/README.md`
  - `tracks/multimodal/README.md`
  - `tracks/agentic/README.md`
  - `tracks/harness/README.md`
  - `cases/bigtech/README.md`
  - `cases/mid_company/README.md`
  - `cases/small_team/README.md`
- Validation:
  - 文档文件已创建并可读取
  - 顶层 README 已能指向新的总纲、学习路径、tracks 和 cases
  - runbook 与 code map 已补上 V2 语义说明
- Next step:
  - 建立 `Coding` 与 `Harness` 的第一批任务文档骨架
  - 补一个真正可展示提升的 `Post-Training` golden path
  - 逐步把旧 `T00-T32` 任务补写成符合 V2 模板的版本

## Session Entry

- Date: 2026-04-05 19:49-20:00 CST
- Goal: 了解 `llm-engineering-lab` 结构，并执行第一轮高价值优化。
- Status: 已完成项目盘点和缺口定位，正在实现 Stage 3 推理增强最小链路。
- Key findings:
  - 仓库不是完整训练框架，而是面向工程师的教学/演练仓库。
  - 代码实现目前只到 `stage2_sft`，但文档路线已经延伸到 reasoning / verifier / toy alignment。
  - 最大的上手阻塞不是模型代码本身，而是“文档承诺和实际文件不一致”。
  - `datasets/tiny_reasoning/*.jsonl` 已准备好，可直接作为 Stage 3 最小实现的数据源。
  - `eval/sft_eval.py` 已经提供了 checkpoint 加载和文本生成的复用模式，新增 reasoning 评测时应沿用同样结构。
- Files inspected:
  - `README.md`
  - `docs/runbook.md`
  - `docs/project_charter.md`
  - `code/README.md`
  - `code/stage1_nanogpt_core/train.py`
  - `code/stage1_nanogpt_core/model.py`
  - `code/stage2_sft/train_sft.py`
  - `code/stage2_sft/dataset.py`
  - `eval/sft_eval.py`
  - `datasets/README.md`
  - `datasets/tiny_reasoning/train.jsonl`
  - `datasets/tiny_reasoning/eval.jsonl`
- Files touched:
  - `docs/session_handoff.md`
- Validation:
  - 目录扫描确认当前存在 `eval/sft_eval.py`，不存在 `eval/reasoning_eval.py`
  - 目录扫描确认当前不存在 `code/stage3_reasoning`
  - 数据格式确认 `tiny_reasoning` 为 `{question, rationale, answer}`
- Next step:
  - 新增 `code/stage3_reasoning/`，实现单题多候选采样和 self-consistency 聚合
  - 新增 `eval/reasoning_eval.py`
  - 对齐 README / runbook 的实际命令

## Session Entry

- Date: 2026-04-05 20:00-20:45 CST
- Goal: 补齐 Stage 3 最小推理增强链路，并把仓库文档对齐到实际实现状态。
- Status: 已完成 Stage 3 最小实现、基本 smoke 验证和文档同步。
- Key findings:
  - `MiniGPT.generate()` 原先只有采样路径，没有真正的 greedy 模式；已补上 `temperature <= 0` 时走 `argmax`。
  - 由于项目使用字符级 tokenizer，Stage 3 新 prompt 一开始会因为未见过的字符直接报错。
  - 已在 `stage3_reasoning/self_consistency.py` 增加 tokenizer 兼容层，会优先保留原字符，其次尝试大小写回退，最后降级为空格。
  - 用 2 step 的 `stage2_sft_smoke` checkpoint 验证后，Stage 3 脚本已经可以完整跑通，但准确率接近 0，这说明现在验证的是“链路可运行”，不是“模型已具备 reasoning 能力”。
  - `code/stage4_verifier/` 和 `code/stage5_toy_alignment/` 当前是空目录，之前 runbook 中的命令是不可执行承诺，已改成明确说明“尚未实现”。
- Files touched:
  - `code/stage1_nanogpt_core/model.py`
  - `code/stage3_reasoning/__init__.py`
  - `code/stage3_reasoning/self_consistency.py`
  - `code/stage3_reasoning/sample_reasoning.py`
  - `eval/reasoning_eval.py`
  - `README.md`
  - `docs/runbook.md`
  - `code/README.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m py_compile code/stage1_nanogpt_core/model.py code/stage3_reasoning/self_consistency.py code/stage3_reasoning/sample_reasoning.py eval/reasoning_eval.py`
  - `python3 code/stage2_sft/train_sft.py --init-from runs/stage1_gpt/ckpt.pt --max-iters 2 --eval-interval 1 --out-dir runs/stage2_sft_smoke`
  - `python3 code/stage3_reasoning/sample_reasoning.py --checkpoint runs/stage2_sft_smoke/ckpt.pt --question "A ticket spends 12 minutes in triage and 18 minutes in repair. How long is the total?" --num-samples 3 --max-new-tokens 40`
  - `python3 eval/reasoning_eval.py --checkpoint runs/stage2_sft_smoke/ckpt.pt --data-path datasets/tiny_reasoning/eval.jsonl --num-samples 3 --max-new-tokens 40`
  - smoke 结果: 脚本运行成功，但输出仍接近随机，`greedy_exact=0.000`，`self_consistency_exact=0.000`
- Next step:
  - 决定是否继续补 `stage2` 的 reasoning trace SFT 数据路径，让 Stage 3 不只可运行，还能在 tiny_reasoning 上获得非零效果
  - 如果继续做 Stage 4，则先实现最小 verifier 数据读入、打分模型和 rerank 脚本
  - 如果暂停开发，下次先检查 `runs/stage2_sft_smoke/` 是否还在，再决定是复用 smoke checkpoint 还是重新训练更长的 `runs/stage2_sft/`

## Session Entry

- Date: 2026-04-05 20:45-21:20 CST
- Goal: 把 `tiny_reasoning` 接进 Stage 2 SFT 路径，验证 reasoning-trace 微调是否能带来可观测收益。
- Status: 已完成数据通路、长上下文自动扩展、`sft_eval` 修复和两轮 reasoning-trace 训练验证。
- Key findings:
  - `tiny_reasoning` 的 prompt 长度约 338 token，原始 `block_size=192` 会截断大部分提示词，这是之前 reasoning 路线效果很差的关键原因之一。
  - `train_sft.py` 现在支持同时读取普通 instruction 数据和 reasoning 数据，reasoning 行会自动转换成 `Reasoning: ...` 加 `Final Answer: ...` 的 assistant 输出。
  - `train_sft.py` 现在会根据训练和评测样本的最长 token 长度自动扩展 `block_size`。在 mixed reasoning 训练中，`block_size` 自动扩展到了 432。
  - 混合训练和 reasoning-only 继续训练都已经打通，输出开始出现 `Reasoning` / `Answer` 相关结构，但 tiny base checkpoint 依然太弱，`reasoning_eval.py` 仍未取得非零 exact match。
  - `eval/sft_eval.py` 之前有两类历史问题: `sys.path` 指向错误，以及 base tokenizer 遇到未见字符直接跳过。两者都已修复。
- Files touched:
  - `code/stage2_sft/dataset.py`
  - `code/stage2_sft/train_sft.py`
  - `code/stage3_reasoning/self_consistency.py`
  - `eval/sft_eval.py`
  - `README.md`
  - `docs/runbook.md`
  - `datasets/README.md`
  - `code/README.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m py_compile code/stage2_sft/dataset.py code/stage2_sft/train_sft.py code/stage3_reasoning/self_consistency.py eval/sft_eval.py`
  - mixed reasoning trace:
    `python3 code/stage2_sft/train_sft.py --init-from runs/stage1_gpt/ckpt.pt --data-path datasets/tiny_sft/train.jsonl datasets/tiny_reasoning/train.jsonl --eval-path datasets/tiny_sft/eval.jsonl datasets/tiny_reasoning/eval.jsonl --max-iters 240 --eval-interval 80 --learning-rate 3e-4 --out-dir runs/stage2_reasoning_trace_longctx`
  - reasoning-only continuation:
    `python3 code/stage2_sft/train_sft.py --init-from runs/stage2_reasoning_trace_longctx/ckpt.pt --data-path datasets/tiny_reasoning/train.jsonl --eval-path datasets/tiny_reasoning/eval.jsonl --max-iters 600 --eval-interval 200 --learning-rate 3e-4 --out-dir runs/stage2_reasoning_only_longctx`
  - eval:
    `python3 eval/reasoning_eval.py --checkpoint runs/stage2_reasoning_trace_longctx/ckpt.pt --data-path datasets/tiny_reasoning/eval.jsonl --num-samples 5 --max-new-tokens 80`
    `python3 eval/reasoning_eval.py --checkpoint runs/stage2_reasoning_only_longctx/ckpt.pt --data-path datasets/tiny_reasoning/eval.jsonl --num-samples 5 --max-new-tokens 80`
    `python3 eval/sft_eval.py --checkpoint runs/stage2_reasoning_only_longctx/ckpt.pt --base-checkpoint runs/stage1_gpt/ckpt.pt --data-path datasets/tiny_sft/eval.jsonl --max-new-tokens 80`
  - 当前结果:
    - `stage2_reasoning_trace_longctx`: `any_candidate_hit=0.250`, exact match 仍为 0
    - `stage2_reasoning_only_longctx`: `any_candidate_hit=0.250`, exact match 仍为 0
    - 说明链路、上下文和输出格式已改善，但 base checkpoint 质量仍不足以支撑 tiny reasoning 任务
- Next step:
  - 如果继续追求效果，优先加强 `stage1_gpt` 预训练质量或直接提供一个更强的 teacher-like Stage 2 checkpoint 作为 reasoning 起点
  - 如果继续扩仓库能力，转向实现 `stage4_verifier` 更划算，因为当前 generator 已能产出多个候选但质量不稳定
  - 如果下次接着做，先复用 `runs/stage2_reasoning_trace_longctx/` 和 `runs/stage2_reasoning_only_longctx/`，不要重复从头训练

## Session Entry

- Date: 2026-04-05 21:20-21:40 CST
- Goal: 实现 Stage 4 verifier 的最小训练与 rerank 闭环。
- Status: 已完成 verifier 模型、数值特征、训练脚本和 demo rerank 验证。
- Key findings:
  - 纯字符平均池化 verifier 几乎不学习，训练 400 step 仍停在 0.5 accuracy 左右。
  - 对当前 tiny arithmetic 数据，更合理的 verifier 不是“只看文本像不像对”，而是“文本表征 + 最终答案是否和题目数值一致”。
  - 新版 verifier 在 `prompt` 和 `candidate` 的字符级表征之外，还加入了 6 维数值一致性特征，包括是否能解析 prompt、是否存在 `Final Answer`、候选答案类型是否匹配、是否 exact match、以及 closeness。
  - 这版模型在 `tiny_verifier/train.jsonl` 上可以收敛到 `train_accuracy=8/8`，并且在 `demo_candidates.jsonl` 上把正确候选稳定排到第一。
- Files touched:
  - `code/stage4_verifier/__init__.py`
  - `code/stage4_verifier/model.py`
  - `code/stage4_verifier/features.py`
  - `code/stage4_verifier/train_verifier.py`
  - `code/stage4_verifier/rerank.py`
  - `README.md`
  - `docs/runbook.md`
  - `code/README.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m py_compile code/stage4_verifier/model.py code/stage4_verifier/features.py code/stage4_verifier/train_verifier.py code/stage4_verifier/rerank.py`
  - `python3 code/stage4_verifier/train_verifier.py --max-iters 200 --eval-interval 50 --learning-rate 1e-3 --out-dir runs/stage4_verifier`
  - `python3 code/stage4_verifier/rerank.py --checkpoint runs/stage4_verifier/ckpt.pt --prompt-file datasets/tiny_verifier/demo_candidates.jsonl`
  - 训练结果: `step 199: loss=0.1994 accuracy=1.000`
  - rerank 结果: `Subtract 9 from 16. Final Answer: 7` 被排到第 1，分数 `0.850`
- Next step:
  - 把 `stage3_reasoning` 的多候选输出直接接到 verifier rerank，而不是只在静态 demo 文件上重排
  - 增加一个对照评测，比较 self-consistency 与 verifier rerank 在同一问题集上的差别
  - 如果继续扩范围，再开始 `stage5_toy_alignment`

## Session Entry

- Date: 2026-04-05 21:40-21:55 CST
- Goal: 把 Stage 4 verifier 接到 Stage 3 多候选推理链路，并输出同场对照评测。
- Status: 已完成链路集成，`sample_reasoning.py` 和 `reasoning_eval.py` 现在都支持 `--verifier-checkpoint`。
- Key findings:
  - `stage4_verifier/rerank.py` 已被抽成可复用接口，Stage 3 可以直接调用它对同一批采样候选做重排。
  - 为了适配 verifier 的数值特征，Stage 3 现在会在候选缺少显式 `Final Answer:` 时自动补上标准化答案行再送入 scorer。
  - 集成后的 `reasoning_eval.py` 会同时输出 `greedy_exact`、`self_consistency_exact`、`verifier_rerank_exact` 和平均 scored candidates 数。
  - 当前结果依然是 `verifier_rerank_exact=0.000`，不是集成失效，而是因为 generator 在这批 tiny eval 候选里本身就没有采到正确答案，`any_candidate_hit=0.000`。这验证了一个关键工程结论: rerank 只能筛选已有候选，不能替代候选生成质量。
- Files touched:
  - `code/stage3_reasoning/self_consistency.py`
  - `code/stage3_reasoning/sample_reasoning.py`
  - `code/stage4_verifier/rerank.py`
  - `eval/reasoning_eval.py`
  - `docs/runbook.md`
  - `code/README.md`
  - `docs/session_handoff.md`
- Validation:
  - `python3 -m py_compile code/stage3_reasoning/self_consistency.py code/stage3_reasoning/sample_reasoning.py code/stage4_verifier/rerank.py eval/reasoning_eval.py`
  - `python3 code/stage3_reasoning/sample_reasoning.py --checkpoint runs/stage2_reasoning_only_longctx/ckpt.pt --verifier-checkpoint runs/stage4_verifier/ckpt.pt --question "A queue has 16 messages and 9 are processed. How many are left?" --num-samples 5 --max-new-tokens 80`
  - `python3 eval/reasoning_eval.py --checkpoint runs/stage2_reasoning_only_longctx/ckpt.pt --verifier-checkpoint runs/stage4_verifier/ckpt.pt --data-path datasets/tiny_reasoning/eval.jsonl --num-samples 5 --max-new-tokens 80`
  - 当前结果:
    - `greedy_exact=0.000`
    - `self_consistency_exact=0.000`
    - `verifier_rerank_exact=0.000`
    - `any_candidate_hit=0.000`
    - `avg_verifier_candidates_scored=5.0`
- Next step:
  - 如果要继续提升 Sprint 3 效果，优先增强 generator，让 sampled candidates 里先出现正确答案
  - verifier 路线已经足够完整，除非要扩数据或做更强 scorer，否则没必要继续在当前 tiny 候选池上打磨
  - 接下来更自然的方向是 `stage5_toy_alignment`

## 恢复工作时先看这几件事

1. 先读本文件的最新 `Session Entry`
2. 检查 `code/stage3_reasoning/` 和 `eval/reasoning_eval.py` 是否已经创建
3. 如果脚本已存在，先运行最小命令验证:

```bash
python3 eval/reasoning_eval.py --checkpoint runs/stage2_sft/ckpt.pt --data-path datasets/tiny_reasoning/eval.jsonl --num-samples 5
```

4. 如果验证失败，优先记录:
   - 是 checkpoint 缺失
   - 是 tokenizer / prompt 格式问题
   - 还是聚合逻辑本身有 bug

## 已确认的实现边界

- 当前项目的 tokenizer 是字符级 `CharTokenizer`
- 当前生成模型是 `stage1_nanogpt_core/model.py` 里的 `MiniGPT`
- Stage 2 SFT 已能加载 base checkpoint 并扩充 tokenizer
- Stage 3 的第一版应该尽量复用现有模型和 prompt 机制，避免引入新训练路径
- 现阶段先补“推理时增强”，不要提前引入 Stage 4/5 的训练复杂度
