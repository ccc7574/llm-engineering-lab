from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_coding.bugfix_dataset import load_bugfix_tasks
from stage_coding.bugfix_runner import build_candidate
from stage_coding.execution import evaluate_python_candidate


@dataclass
class BugfixResult:
    task_id: str
    strategy: str
    passed: bool
    failure_type: str | None
    failure_message: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_bugfix/eval.jsonl")
    parser.add_argument("--strategy", choices=["buggy", "heuristic", "reference"], default="heuristic")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_bugfix_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        candidate = build_candidate(task, args.strategy)
        execution = evaluate_python_candidate(candidate=candidate, tests=task.tests)
        result = BugfixResult(
            task_id=task.task_id,
            strategy=args.strategy,
            passed=execution.passed,
            failure_type=execution.failure_type,
            failure_message=execution.failure_message,
        )
        results.append(result)
        status = "pass" if result.passed else "fail"
        print(f"{task.task_id}: {status}")
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
        "results": [asdict(result) for result in results],
    }
    print(f"pass@1={summary['pass_at_1']:.3f} ({passed}/{len(results)})")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
