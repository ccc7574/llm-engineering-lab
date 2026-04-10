from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_coding.passk_dataset import PassKCandidate, PassKTask, load_passk_tasks


@dataclass
class PassKSelection:
    task_id: str
    strategy: str
    k: int
    selected_sample_ids: list[str]
    candidates_sampled: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_coding_passk/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--strategy", choices=["single_sample", "sample_k", "reference"], default="sample_k")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def select_candidates(task: PassKTask, strategy: str, k: int) -> list[PassKCandidate]:
    if strategy == "reference":
        return [task.candidates[-1]]
    if strategy == "single_sample":
        return task.candidates[:1]
    return task.candidates[: max(1, min(k, len(task.candidates)))]


def build_selection(task: PassKTask, strategy: str, k: int) -> PassKSelection:
    selected = select_candidates(task, strategy, k)
    return PassKSelection(
        task_id=task.task_id,
        strategy=strategy,
        k=max(1, k),
        selected_sample_ids=[candidate.sample_id for candidate in selected],
        candidates_sampled=len(selected),
    )


def main() -> None:
    args = parse_args()
    tasks = load_passk_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        selection = build_selection(task, args.strategy, args.k)
        print(f"Task: {task.task_id}")
        print(f"Selected samples: {selection.selected_sample_ids}")
        print("-" * 72)
        rows.append(asdict(selection))

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved pass@k selections to {output_path}")


if __name__ == "__main__":
    main()
