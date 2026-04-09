from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_coding.testgen_dataset import TestGenTask, load_testgen_tasks


@dataclass
class TestGenCandidate:
    task_id: str
    strategy: str
    tests: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_testgen/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--strategy", choices=["weak", "targeted", "reference"], default="targeted")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def weak_tests(task: TestGenTask) -> list[str]:
    tests = {
        "normalize_env_name_testgen": ["assert normalize_env_name('PROD') == 'prod'"],
        "retry_budget_testgen": ["assert retry_budget(3) == 6"],
        "build_alert_title_testgen": ["assert build_alert_title('payments', 'sev1') == 'payments:sev1'"],
    }
    return tests.get(task.task_id, [])


def targeted_tests(task: TestGenTask) -> list[str]:
    tests = {
        "normalize_env_name_testgen": [
            "assert normalize_env_name('PROD') == 'prod'",
            "assert normalize_env_name(' Staging ') == 'staging'",
        ],
        "retry_budget_testgen": [
            "assert retry_budget(3) == 6",
            "assert retry_budget(0) == 0",
        ],
        "build_alert_title_testgen": [
            "assert build_alert_title('payments', 'sev1') == 'payments:critical'",
            "assert build_alert_title('search', 'sev2') == 'search:major'",
        ],
    }
    return tests.get(task.task_id, weak_tests(task))


def build_test_candidate(task: TestGenTask, strategy: str) -> TestGenCandidate:
    if strategy == "reference":
        tests = list(task.tests_should_include)
    elif strategy == "targeted":
        tests = targeted_tests(task)
    else:
        tests = weak_tests(task)
    return TestGenCandidate(task_id=task.task_id, strategy=strategy, tests=tests)


def main() -> None:
    args = parse_args()
    tasks = load_testgen_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        candidate = build_test_candidate(task, args.strategy)
        print(f"Task: {task.task_id}")
        for test in candidate.tests:
            print(test)
        print("-" * 72)
        rows.append(asdict(candidate))

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved generated tests to {output_path}")


if __name__ == "__main__":
    main()
