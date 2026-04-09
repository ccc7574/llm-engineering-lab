from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_coding.bugfix_dataset import BugfixTask, load_bugfix_tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_bugfix/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--strategy", choices=["buggy", "heuristic", "reference"], default="heuristic")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def heuristic_fix(task: BugfixTask) -> str:
    fixes = {
        "sum_even_numbers_bugfix": (
            "def sum_even_numbers(values: list[int]) -> int:\n"
            "    total = 0\n"
            "    for value in values:\n"
            "        if value % 2 == 0:\n"
            "            total += value\n"
            "    return total"
        ),
        "normalize_username_bugfix": (
            "def normalize_username(text: str) -> str:\n"
            "    return text.strip().lower().replace(' ', '_')"
        ),
        "build_status_line_bugfix": (
            "def build_status_line(service: str, status: str) -> str:\n"
            "    return f'{service}: {status}'"
        ),
        "minutes_to_hours_bugfix": (
            "def minutes_to_hours(minutes: int) -> float:\n"
            "    return minutes / 60"
        ),
        "normalize_service_name_bugfix": (
            "def normalize_service_name(name: str) -> str:\n"
            "    return name.strip().lower()"
        ),
        "render_incident_key_bugfix": (
            "def render_incident_key(service: str, incident_id: int) -> str:\n"
            "    return f'{service}#{incident_id}'"
        ),
    }
    return fixes.get(task.task_id, task.buggy_code)


def build_candidate(task: BugfixTask, strategy: str) -> str:
    if strategy == "reference":
        return task.canonical_fix
    if strategy == "heuristic":
        return heuristic_fix(task)
    return task.buggy_code


def main() -> None:
    args = parse_args()
    tasks = load_bugfix_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        candidate = build_candidate(task, args.strategy)
        print(f"Task: {task.task_id}")
        print(f"Issue: {task.issue}")
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
