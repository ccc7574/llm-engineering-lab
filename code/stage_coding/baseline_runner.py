from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_coding.dataset import CodingTask, load_coding_tasks
from stage_coding.prompt_template import render_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_coding/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--strategy", choices=["weak", "heuristic", "reference"], default="heuristic")
    parser.add_argument("--show-prompt", action="store_true")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def weak_solution(task: CodingTask) -> str:
    return task.starter_code.replace("raise NotImplementedError", "return None")


def heuristic_solution(task: CodingTask) -> str:
    implementations = {
        "add_numbers": "def add_numbers(a: int, b: int) -> int:\n    return a + b",
        "is_even": "def is_even(n: int) -> bool:\n    return n % 2 == 0",
        "clamp": (
            "def clamp(value: int, lower: int, upper: int) -> int:\n"
            "    if value < lower:\n"
            "        return lower\n"
            "    if value > upper:\n"
            "        return upper\n"
            "    return value"
        ),
        "count_words": (
            "def count_words(text: str) -> int:\n"
            "    stripped = text.strip()\n"
            "    if not stripped:\n"
            "        return 0\n"
            "    return len(stripped.split())"
        ),
        "reverse_string": "def reverse_string(text: str) -> str:\n    return text[::-1]",
        "sum_positive": (
            "def sum_positive(values: list[int]) -> int:\n"
            "    total = 0\n"
            "    for value in values:\n"
            "        if value > 0:\n"
            "            total += value\n"
            "    return total"
        ),
        "normalize_ticket_id": (
            "def normalize_ticket_id(text: str) -> str:\n"
            "    cleaned = text.strip().upper()\n"
            "    return '-'.join(cleaned.split())"
        ),
    }
    if task.task_id not in implementations:
        return weak_solution(task)
    return implementations[task.task_id]


def build_candidate(task: CodingTask, strategy: str) -> str:
    if strategy == "reference":
        return task.canonical_solution
    if strategy == "heuristic":
        return heuristic_solution(task)
    return weak_solution(task)


def main() -> None:
    args = parse_args()
    tasks = load_coding_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        candidate = build_candidate(task, args.strategy)
        if args.show_prompt:
            print(f"Task: {task.task_id}")
            print(render_prompt(task))
        print(f"Task: {task.task_id}")
        print(candidate)
        print("-" * 72)
        rows.append({"task_id": task.task_id, "strategy": args.strategy, "candidate": candidate})

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved candidates to {output_path}")


if __name__ == "__main__":
    main()
