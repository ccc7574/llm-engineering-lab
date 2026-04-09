from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_coding.execution import evaluate_python_patch
from stage_coding.multifile_bugfix_dataset import load_multifile_bugfix_tasks
from stage_coding.patch_runner import build_patch_candidate


@dataclass
class MultiFileBugfixResult:
    task_id: str
    strategy: str
    passed: bool
    failure_type: str | None
    failure_message: str | None
    touched_files_count: int
    patch_recall: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_multifile_bugfix/eval.jsonl")
    parser.add_argument("--strategy", choices=["single_file", "patch_protocol", "reference"], default="patch_protocol")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_multifile_bugfix_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        candidate = build_patch_candidate(task, args.strategy)
        execution = evaluate_python_patch(
            repo_files=task.repo_files,
            patch_files=candidate.patch_files,
            tests=task.tests,
            execution_order=task.execution_order,
        )
        result = MultiFileBugfixResult(
            task_id=task.task_id,
            strategy=args.strategy,
            passed=execution.passed,
            failure_type=execution.failure_type,
            failure_message=execution.failure_message,
            touched_files_count=len(candidate.touched_files),
            patch_recall=candidate.patch_recall,
        )
        results.append(result)
        status = "pass" if result.passed else "fail"
        print(f"{task.task_id}: {status}")
        print(
            f"  touched_files_count={result.touched_files_count} "
            f"patch_recall={result.patch_recall:.2f}"
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
        "avg_touched_files_count": sum(result.touched_files_count for result in results) / total,
        "avg_patch_recall": sum(result.patch_recall for result in results) / total,
        "results": [asdict(result) for result in results],
    }
    print(f"pass@1={summary['pass_at_1']:.3f} ({passed}/{len(results)})")
    print(f"avg_touched_files_count={summary['avg_touched_files_count']:.2f}")
    print(f"avg_patch_recall={summary['avg_patch_recall']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
