from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_coding.testgen_dataset import load_testgen_tasks
from stage_coding.testgen_runner import build_test_candidate


@dataclass
class TestGenResult:
    task_id: str
    strategy: str
    reference_passes: bool
    buggy_caught: bool
    useful: bool
    generated_tests_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_testgen/eval.jsonl")
    parser.add_argument("--strategy", choices=["weak", "targeted", "reference"], default="targeted")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def run_tests(source: str, tests: list[str]) -> bool:
    namespace: dict[str, object] = {}
    exec(source, namespace, namespace)
    try:
        for test in tests:
            exec(test, namespace, namespace)
    except Exception:  # noqa: BLE001
        return False
    return True


def main() -> None:
    args = parse_args()
    tasks = load_testgen_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        candidate = build_test_candidate(task, args.strategy)
        reference_passes = run_tests(task.reference_code, candidate.tests)
        buggy_passes = run_tests(task.buggy_code, candidate.tests)
        buggy_caught = not buggy_passes
        useful = reference_passes and buggy_caught
        result = TestGenResult(
            task_id=task.task_id,
            strategy=args.strategy,
            reference_passes=reference_passes,
            buggy_caught=buggy_caught,
            useful=useful,
            generated_tests_count=len(candidate.tests),
        )
        results.append(result)
        status = "pass" if useful else "fail"
        print(f"{task.task_id}: {status}")
        print(
            f"  reference_passes={reference_passes} buggy_caught={buggy_caught} "
            f"generated_tests_count={len(candidate.tests)}"
        )

    useful_count = sum(1 for result in results if result.useful)
    total = max(len(results), 1)
    summary = {
        "strategy": args.strategy,
        "bug_detection_rate": useful_count / total,
        "useful": useful_count,
        "total": len(results),
        "avg_generated_tests_count": sum(result.generated_tests_count for result in results) / total,
        "results": [asdict(result) for result in results],
    }
    print(f"bug_detection_rate={summary['bug_detection_rate']:.3f} ({useful_count}/{len(results)})")
    print(f"avg_generated_tests_count={summary['avg_generated_tests_count']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
