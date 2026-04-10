from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_coding.execution import evaluate_python_patch
from stage_coding.swebench_dataset import load_swebench_lite_tasks
from stage_coding.swebench_runner import build_run


@dataclass
class SwebenchEvalResult:
    task_id: str
    strategy: str
    passed: bool
    failure_type: str | None
    failure_message: str | None
    repo_reads: int
    test_runs: int
    patch_attempts: int
    triage_reads: int
    relevant_context_recall: float
    patch_recall: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_swebench_lite/eval.jsonl")
    parser.add_argument("--strategy", choices=["issue_localized", "triage_loop", "reference"], default="triage_loop")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_swebench_lite_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        run = build_run(task, args.strategy)
        execution = evaluate_python_patch(
            repo_files=task.repo_files,
            patch_files=run.final_patch_files,
            tests=task.tests,
            execution_order=task.execution_order,
        )
        result = SwebenchEvalResult(
            task_id=task.task_id,
            strategy=args.strategy,
            passed=execution.passed,
            failure_type=execution.failure_type,
            failure_message=execution.failure_message,
            repo_reads=run.repo_reads,
            test_runs=run.test_runs,
            patch_attempts=run.patch_attempts,
            triage_reads=run.triage_reads,
            relevant_context_recall=run.relevant_context_recall,
            patch_recall=run.patch_recall,
        )
        results.append(result)
        status = "pass" if result.passed else "fail"
        print(f"{task.task_id}: {status}")
        print(
            f"  repo_reads={result.repo_reads} test_runs={result.test_runs} "
            f"patch_attempts={result.patch_attempts} triage_reads={result.triage_reads}"
        )
        print(
            f"  relevant_context_recall={result.relevant_context_recall:.2f} "
            f"patch_recall={result.patch_recall:.2f}"
        )
        if not result.passed:
            print(f"  failure_type={result.failure_type}")
            print(f"  failure_message={result.failure_message}")

    passed = sum(1 for result in results if result.passed)
    total = max(len(results), 1)
    summary = {
        "strategy": args.strategy,
        "task_success_rate": passed / total,
        "passed": passed,
        "total": len(results),
        "avg_repo_reads": sum(result.repo_reads for result in results) / total,
        "avg_test_runs": sum(result.test_runs for result in results) / total,
        "avg_patch_attempts": sum(result.patch_attempts for result in results) / total,
        "avg_triage_reads": sum(result.triage_reads for result in results) / total,
        "avg_relevant_context_recall": sum(result.relevant_context_recall for result in results) / total,
        "avg_patch_recall": sum(result.patch_recall for result in results) / total,
        "results": [asdict(result) for result in results],
    }
    print(f"task_success_rate={summary['task_success_rate']:.3f} ({passed}/{len(results)})")
    print(f"avg_repo_reads={summary['avg_repo_reads']:.2f}")
    print(f"avg_test_runs={summary['avg_test_runs']:.2f}")
    print(f"avg_patch_attempts={summary['avg_patch_attempts']:.2f}")
    print(f"avg_triage_reads={summary['avg_triage_reads']:.2f}")
    print(f"avg_relevant_context_recall={summary['avg_relevant_context_recall']:.2f}")
    print(f"avg_patch_recall={summary['avg_patch_recall']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
