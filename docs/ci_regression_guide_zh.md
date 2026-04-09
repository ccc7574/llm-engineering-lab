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
- summary board:
  - `runs/summary_board.json`
  - `runs/summary_board.md`
- gate report:
  - `runs/gate_report.json`

## 本地怎么跑

最常用的命令有两种。

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
7. 把 suite report 和 summary board 写进 GitHub Job Summary

对 `pull_request`，workflow 现在会默认尝试按 changed files 跑 scoped suite。

如果变更命中了 `harness` 相关路径，则会自动升级成全量 suite。

## 怎么看结果

最重要的三个 artifact 是:

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
- Multimodal
- Multimodal Noisy OCR
- Run Registry
- Summary Board
- Gate Check

当前 suite 执行策略还包括:

- `changed-scoped`
- `changed-scoped-full`
- `full`
- step 级最小重试

## 当前还没做的部分

这套系统已经够支撑最小交付，但离真实一线团队的完整平台还有几步:

- 定时回归后的通知与值班机制
- latency / cost 趋势面板
- PR comment / release note 自动生成
- flaky 分类与按失败类型决定是否重试
- 更精细的 changed-scope 依赖图，而不只是 scope tag

## 建议的团队使用方式

对这个仓库，推荐按下面方式使用:

1. 本地先跑 `--strict --require-ship`
2. 提 PR 后让 GitHub Actions 自动再跑一遍
3. 合并到 `main` 后保留 artifact，作为一次可复盘的发布前证据
4. 定时任务每天或每周跑一次，防止多条能力线之间出现静默回归
