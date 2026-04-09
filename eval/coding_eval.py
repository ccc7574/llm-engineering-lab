from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_coding.baseline_runner import build_candidate
from stage_coding.dataset import CodingTask, load_coding_tasks


@dataclass
class CandidateResult:
    task_id: str
    strategy: str
    passed: bool
    failure_type: str | None
    failure_message: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_coding/eval.jsonl")
    parser.add_argument("--strategy", choices=["weak", "heuristic", "reference"], default="heuristic")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def evaluate_candidate(task: CodingTask, candidate: str, strategy: str) -> CandidateResult:
    try:
        ast.parse(candidate)
    except SyntaxError as exc:
        return CandidateResult(
            task_id=task.task_id,
            strategy=strategy,
            passed=False,
            failure_type="syntax_error",
            failure_message=str(exc),
        )

    namespace: dict[str, object] = {}
    try:
        exec(candidate, namespace, namespace)
    except Exception as exc:  # noqa: BLE001
        return CandidateResult(
            task_id=task.task_id,
            strategy=strategy,
            passed=False,
            failure_type="runtime_error",
            failure_message=str(exc),
        )

    for test in task.tests:
        try:
            exec(test, namespace, namespace)
        except AssertionError:
            return CandidateResult(
                task_id=task.task_id,
                strategy=strategy,
                passed=False,
                failure_type="assertion_failed",
                failure_message=test,
            )
        except Exception as exc:  # noqa: BLE001
            return CandidateResult(
                task_id=task.task_id,
                strategy=strategy,
                passed=False,
                failure_type="test_runtime_error",
                failure_message=f"{test} | {exc}",
            )

    return CandidateResult(
        task_id=task.task_id,
        strategy=strategy,
        passed=True,
        failure_type=None,
        failure_message=None,
    )


def main() -> None:
    args = parse_args()
    tasks = load_coding_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        candidate = build_candidate(task, args.strategy)
        result = evaluate_candidate(task, candidate, args.strategy)
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
