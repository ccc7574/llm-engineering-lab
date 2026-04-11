from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage3_reasoning.rejection_sampling import build_training_rows, load_rejection_tasks, run_selection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_reasoning_rejection/eval.jsonl")
    parser.add_argument("--strategy", choices=["consensus", "rejection_sampling"], default="rejection_sampling")
    parser.add_argument("--min-verifier-score", type=float, default=0.85)
    parser.add_argument("--report-path", default=None)
    parser.add_argument("--accepted-output", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_rejection_tasks(args.data_path)
    results = run_selection(tasks, args.strategy, args.min_verifier_score)

    accepted = [result for result in results if result.accepted]
    successes = sum(1 for result in results if result.success)
    total = max(len(results), 1)
    accepted_total = max(len(accepted), 1)
    summary = {
        "strategy": args.strategy,
        "task_success_rate": successes / total,
        "acceptance_rate": len(accepted) / total,
        "accepted_precision": sum(1 for result in accepted if result.success) / accepted_total if accepted else 0.0,
        "avg_sampled_candidates": sum(result.sampled_candidates for result in results) / total,
        "avg_accepted_candidates": sum(result.accepted_candidates for result in results) / total,
        "avg_rejected_candidates": sum(result.rejected_candidates for result in results) / total,
        "avg_scored_candidates": sum(result.sampled_candidates for result in results) / total,
        "avg_selected_verifier_score": (
            sum(result.verifier_score for result in accepted) / accepted_total if accepted else 0.0
        ),
        "results": [result.__dict__ for result in results],
    }

    print(f"task_success_rate={summary['task_success_rate']:.3f} ({successes}/{len(results)})")
    print(f"acceptance_rate={summary['acceptance_rate']:.3f} ({len(accepted)}/{len(results)})")
    print(f"accepted_precision={summary['accepted_precision']:.3f}")
    print(f"avg_sampled_candidates={summary['avg_sampled_candidates']:.2f}")
    print(f"avg_accepted_candidates={summary['avg_accepted_candidates']:.2f}")
    print(f"avg_rejected_candidates={summary['avg_rejected_candidates']:.2f}")
    print(f"avg_scored_candidates={summary['avg_scored_candidates']:.2f}")
    print(f"avg_selected_verifier_score={summary['avg_selected_verifier_score']:.3f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")
    if args.accepted_output:
        accepted_output = Path(args.accepted_output)
        ensure_dir(accepted_output.parent)
        rows = build_training_rows(tasks, results)
        accepted_output.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        print(f"saved accepted dataset to {accepted_output}")


if __name__ == "__main__":
    main()
