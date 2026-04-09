from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_coding.dataset import load_coding_tasks
from stage_coding.execution import build_context_prelude, evaluate_python_candidate
from stage_coding.repo_context_runner import build_candidate


@dataclass
class RepoContextResult:
    task_id: str
    strategy: str
    passed: bool
    failure_type: str | None
    failure_message: str | None
    selected_context_count: int
    relevant_context_recall: float
    context_char_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_repo_context/eval.jsonl")
    parser.add_argument("--strategy", choices=["local_only", "contextual", "retrieved", "reference"], default="retrieved")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_coding_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        candidate_result = build_candidate(task, args.strategy)
        execution = evaluate_python_candidate(
            candidate=candidate_result.candidate,
            tests=task.tests,
            prelude=build_context_prelude(
                {} if args.strategy == "local_only" else {path: task.context_files[path] for path in candidate_result.selected_context_files}
            ),
        )
        result = RepoContextResult(
            task_id=task.task_id,
            strategy=args.strategy,
            passed=execution.passed,
            failure_type=execution.failure_type,
            failure_message=execution.failure_message,
            selected_context_count=len(candidate_result.selected_context_files),
            relevant_context_recall=candidate_result.relevant_context_recall,
            context_char_count=candidate_result.context_char_count,
        )
        results.append(result)
        status = "pass" if result.passed else "fail"
        print(f"{task.task_id}: {status}")
        print(
            f"  selected_context_count={result.selected_context_count} "
            f"relevant_context_recall={result.relevant_context_recall:.2f} "
            f"context_char_count={result.context_char_count}"
        )
        if not result.passed:
            print(f"  failure_type={result.failure_type}")
            print(f"  failure_message={result.failure_message}")

    passed = sum(1 for result in results if result.passed)
    total = max(len(results), 1)
    summary = {
        "strategy": args.strategy,
        "pass_at_1": passed / total,
        "passed": passed,
        "total": len(results),
        "avg_selected_context_count": sum(result.selected_context_count for result in results) / total,
        "avg_relevant_context_recall": sum(result.relevant_context_recall for result in results) / total,
        "avg_context_char_count": sum(result.context_char_count for result in results) / total,
        "results": [asdict(result) for result in results],
    }
    print(f"pass@1={summary['pass_at_1']:.3f} ({passed}/{len(results)})")
    print(f"avg_selected_context_count={summary['avg_selected_context_count']:.2f}")
    print(f"avg_relevant_context_recall={summary['avg_relevant_context_recall']:.2f}")
    print(f"avg_context_char_count={summary['avg_context_char_count']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
