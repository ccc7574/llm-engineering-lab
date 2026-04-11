from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_multimodal.router_sft import heuristic_route, load_route_policy, load_route_tasks, predict_route
from stage_multimodal.task_runner import build_run


@dataclass
class MultimodalSftEvalResult:
    task_id: str
    predicted_strategy: str
    expected_strategy: str
    route_correct: bool
    route_confidence: float
    answer: str
    expected_answer: str
    success: bool
    visual_tokens_used: int
    observation_steps: int
    reasoning_steps: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_multimodal_sft/eval.jsonl")
    parser.add_argument(
        "--strategy",
        choices=["heuristic_router", "learned_router"],
        default="heuristic_router",
    )
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def normalize(text: str) -> str:
    return text.strip().lower()


def main() -> None:
    args = parse_args()
    tasks = load_route_tasks(args.data_path)

    if args.strategy == "learned_router":
        if not args.checkpoint:
            raise SystemExit("--checkpoint is required for learned_router")
        model, feature_vocab = load_route_policy(args.checkpoint)
    else:
        model = None
        feature_vocab = []

    results: list[MultimodalSftEvalResult] = []
    for task in tasks:
        prediction = (
            heuristic_route(task)
            if args.strategy == "heuristic_router"
            else predict_route(model, feature_vocab, task)
        )
        run = build_run(task, prediction.strategy)
        success = normalize(run.answer) == normalize(task.expected_answer)
        route_correct = bool(task.target_strategy) and prediction.strategy == task.target_strategy
        result = MultimodalSftEvalResult(
            task_id=task.task_id,
            predicted_strategy=prediction.strategy,
            expected_strategy=task.target_strategy,
            route_correct=route_correct,
            route_confidence=prediction.confidence,
            answer=run.answer,
            expected_answer=task.expected_answer,
            success=success,
            visual_tokens_used=run.visual_tokens_used,
            observation_steps=run.observation_steps,
            reasoning_steps=run.reasoning_steps,
        )
        results.append(result)
        status = "pass" if success else "fail"
        print(
            f"{task.task_id}: {status} "
            f"predicted_strategy={prediction.strategy} expected_strategy={task.target_strategy or 'n/a'}"
        )
        print(
            f"  answer={run.answer} expected={task.expected_answer} "
            f"route_confidence={prediction.confidence:.3f}"
        )

    total = max(len(results), 1)
    route_total = max(sum(1 for result in results if result.expected_strategy), 1)
    successes = sum(1 for result in results if result.success)
    route_hits = sum(1 for result in results if result.route_correct)
    summary = {
        "strategy": args.strategy,
        "task_success_rate": successes / total,
        "route_accuracy": route_hits / route_total,
        "successes": successes,
        "total": len(results),
        "route_hits": route_hits,
        "route_total": sum(1 for result in results if result.expected_strategy),
        "avg_route_confidence": sum(result.route_confidence for result in results) / total,
        "avg_visual_tokens_used": sum(result.visual_tokens_used for result in results) / total,
        "avg_observation_steps": sum(result.observation_steps for result in results) / total,
        "avg_reasoning_steps": sum(result.reasoning_steps for result in results) / total,
        "results": [asdict(result) for result in results],
    }
    print(f"task_success_rate={summary['task_success_rate']:.3f} ({successes}/{len(results)})")
    print(f"route_accuracy={summary['route_accuracy']:.3f} ({route_hits}/{summary['route_total']})")
    print(f"avg_route_confidence={summary['avg_route_confidence']:.3f}")
    print(f"avg_visual_tokens_used={summary['avg_visual_tokens_used']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
