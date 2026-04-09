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
from stage_coding.judge import score_bugfix_candidate


@dataclass
class BugfixJudgeResult:
    task_id: str
    strategy: str
    selected_label: str
    passed: bool
    total_score: float
    candidates_scored: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_bugfix/eval.jsonl")
    parser.add_argument("--strategy", choices=["first_candidate", "judge_rerank"], default="judge_rerank")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def choose_candidate(task, strategy: str) -> tuple[str, str, float, int, bool]:
    pool = [
        ("buggy", build_candidate(task, "buggy")),
        ("heuristic", build_candidate(task, "heuristic")),
    ]
    if strategy == "first_candidate":
        label, candidate = pool[0]
        score = score_bugfix_candidate(task, candidate)
        return label, candidate, score.total_score, 1, score.passed

    scored = []
    for label, candidate in pool:
        score = score_bugfix_candidate(task, candidate)
        scored.append((score.total_score, label, candidate, score.passed))
    scored.sort(reverse=True)
    total_score, label, candidate, passed = scored[0]
    return label, candidate, total_score, len(pool), passed


def main() -> None:
    args = parse_args()
    tasks = load_bugfix_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        label, _candidate, total_score, candidates_scored, passed = choose_candidate(task, args.strategy)
        result = BugfixJudgeResult(
            task_id=task.task_id,
            strategy=args.strategy,
            selected_label=label,
            passed=passed,
            total_score=total_score,
            candidates_scored=candidates_scored,
        )
        results.append(result)
        status = "pass" if passed else "fail"
        print(f"{task.task_id}: {status}")
        print(
            f"  selected_label={label} total_score={total_score:.2f} "
            f"candidates_scored={candidates_scored}"
        )

    passed = sum(1 for result in results if result.passed)
    total = max(len(results), 1)
    summary = {
        "strategy": args.strategy,
        "pass_at_1": passed / total,
        "passed": passed,
        "total": len(results),
        "avg_total_score": sum(result.total_score for result in results) / total,
        "avg_candidates_scored": sum(result.candidates_scored for result in results) / total,
        "results": [asdict(result) for result in results],
    }
    print(f"pass@1={summary['pass_at_1']:.3f} ({passed}/{len(results)})")
    print(f"avg_total_score={summary['avg_total_score']:.2f}")
    print(f"avg_candidates_scored={summary['avg_candidates_scored']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
