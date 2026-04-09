from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_multimodal.dataset import load_multimodal_tasks
from stage_multimodal.task_runner import build_run


@dataclass
class MultimodalEvalResult:
    task_id: str
    strategy: str
    answer: str
    expected_answer: str
    success: bool
    visual_tokens_used: int
    field_match_rate: float
    extracted_field_count: int
    observation_steps: int
    reasoning_steps: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_multimodal/eval.jsonl")
    parser.add_argument(
        "--strategy",
        choices=["text_only", "vision_augmented", "ocr_only", "structured_pipeline", "reference"],
        default="vision_augmented",
    )
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def normalize(text: str) -> str:
    return text.strip().lower()


def field_match_rate(expected_fields: dict[str, str], predicted_fields: dict[str, str]) -> float:
    if not expected_fields:
        return 0.0
    matches = 0
    for key, expected_value in expected_fields.items():
        if normalize(predicted_fields.get(key, "")) == normalize(expected_value):
            matches += 1
    return matches / max(len(expected_fields), 1)


def main() -> None:
    args = parse_args()
    tasks = load_multimodal_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        run = build_run(task, args.strategy)
        success = normalize(run.answer) == normalize(task.expected_answer)
        result = MultimodalEvalResult(
            task_id=task.task_id,
            strategy=args.strategy,
            answer=run.answer,
            expected_answer=task.expected_answer,
            success=success,
            visual_tokens_used=run.visual_tokens_used,
            field_match_rate=field_match_rate(task.expected_fields, run.extracted_fields),
            extracted_field_count=len(run.extracted_fields),
            observation_steps=run.observation_steps,
            reasoning_steps=run.reasoning_steps,
        )
        results.append(result)
        status = "pass" if success else "fail"
        print(f"{task.task_id}: {status}")
        print(f"  answer={run.answer}")
        print(f"  expected={task.expected_answer}")
        print(
            f"  visual_tokens_used={run.visual_tokens_used} "
            f"field_match_rate={result.field_match_rate:.2f} "
            f"observation_steps={run.observation_steps} reasoning_steps={run.reasoning_steps}"
        )

    successes = sum(1 for result in results if result.success)
    total = max(len(results), 1)
    summary = {
        "strategy": args.strategy,
        "task_success_rate": successes / total,
        "successes": successes,
        "total": len(results),
        "avg_visual_tokens_used": sum(result.visual_tokens_used for result in results) / total,
        "avg_field_match_rate": sum(result.field_match_rate for result in results) / total,
        "avg_extracted_field_count": sum(result.extracted_field_count for result in results) / total,
        "avg_observation_steps": sum(result.observation_steps for result in results) / total,
        "avg_reasoning_steps": sum(result.reasoning_steps for result in results) / total,
        "results": [asdict(result) for result in results],
    }
    print(f"task_success_rate={summary['task_success_rate']:.3f} ({successes}/{len(results)})")
    print(f"avg_visual_tokens_used={summary['avg_visual_tokens_used']:.2f}")
    print(f"avg_field_match_rate={summary['avg_field_match_rate']:.2f}")
    print(f"avg_extracted_field_count={summary['avg_extracted_field_count']:.2f}")
    print(f"avg_observation_steps={summary['avg_observation_steps']:.2f}")
    print(f"avg_reasoning_steps={summary['avg_reasoning_steps']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
