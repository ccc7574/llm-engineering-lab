from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_coding.execution import evaluate_python_candidate
from stage_coding.passk_dataset import load_passk_tasks
from stage_coding.passk_runner import select_candidates


@dataclass
class PassKTaskResult:
    task_id: str
    strategy: str
    k: int
    pass_at_1_hit: bool
    pass_at_k_hit: bool
    candidates_sampled: int
    execution_checks: int
    passing_candidates: int
    first_pass_index: int | None
    selected_sample_ids: list[str]
    selected_failure_types: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_coding_passk/eval.jsonl")
    parser.add_argument("--strategy", choices=["single_sample", "sample_k", "reference"], default="sample_k")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_passk_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        selected = select_candidates(task, args.strategy, args.k)
        passing_candidates = 0
        first_pass_index = None
        failure_types: list[str] = []
        pass_at_1_hit = False

        for index, sample in enumerate(selected, start=1):
            execution = evaluate_python_candidate(candidate=sample.candidate, tests=task.tests)
            if index == 1:
                pass_at_1_hit = execution.passed
            if execution.passed:
                passing_candidates += 1
                if first_pass_index is None:
                    first_pass_index = index
            else:
                failure_types.append(execution.failure_type or "unknown_failure")

        result = PassKTaskResult(
            task_id=task.task_id,
            strategy=args.strategy,
            k=max(1, args.k),
            pass_at_1_hit=pass_at_1_hit,
            pass_at_k_hit=first_pass_index is not None,
            candidates_sampled=len(selected),
            execution_checks=len(selected),
            passing_candidates=passing_candidates,
            first_pass_index=first_pass_index,
            selected_sample_ids=[sample.sample_id for sample in selected],
            selected_failure_types=failure_types,
        )
        results.append(result)
        status = "pass" if result.pass_at_k_hit else "fail"
        print(f"{task.task_id}: {status}")
        print(
            f"  pass_at_1_hit={result.pass_at_1_hit} pass_at_k_hit={result.pass_at_k_hit} "
            f"candidates_sampled={result.candidates_sampled} first_pass_index={result.first_pass_index}"
        )
        print(f"  selected_sample_ids={result.selected_sample_ids}")
        if result.selected_failure_types:
            print(f"  selected_failure_types={result.selected_failure_types}")

    total = max(len(results), 1)
    pass_at_1 = sum(result.pass_at_1_hit for result in results) / total
    pass_at_k = sum(result.pass_at_k_hit for result in results) / total
    pass_count = sum(result.pass_at_k_hit for result in results)
    passing_with_index = [result.first_pass_index for result in results if result.first_pass_index is not None]
    summary = {
        "strategy": args.strategy,
        "k": max(1, args.k),
        "pass_at_1": pass_at_1,
        "pass_at_k": pass_at_k,
        "passed": pass_count,
        "total": len(results),
        "avg_candidates_sampled": sum(result.candidates_sampled for result in results) / total,
        "avg_execution_checks": sum(result.execution_checks for result in results) / total,
        "avg_passing_candidates": sum(result.passing_candidates for result in results) / total,
        "avg_first_pass_index": (
            sum(passing_with_index) / len(passing_with_index) if passing_with_index else 0.0
        ),
        "results": [asdict(result) for result in results],
    }
    print(f"pass@1={summary['pass_at_1']:.3f}")
    print(f"pass@{summary['k']}={summary['pass_at_k']:.3f} ({pass_count}/{len(results)})")
    print(f"avg_candidates_sampled={summary['avg_candidates_sampled']:.2f}")
    print(f"avg_execution_checks={summary['avg_execution_checks']:.2f}")
    print(f"avg_passing_candidates={summary['avg_passing_candidates']:.2f}")
    print(f"avg_first_pass_index={summary['avg_first_pass_index']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
