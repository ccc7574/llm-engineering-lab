from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.io import load_jsonl


@dataclass
class CodingTask:
    task_id: str
    instruction: str
    starter_code: str
    entry_point: str
    canonical_solution: str
    tests: list[str]
    context_files: dict[str, str]
    relevant_context_files: list[str]


def load_coding_tasks(path: str | Path) -> list[CodingTask]:
    rows = load_jsonl(path)
    return [
        CodingTask(
            task_id=row["task_id"],
            instruction=row["instruction"],
            starter_code=row["starter_code"],
            entry_point=row["entry_point"],
            canonical_solution=row["canonical_solution"],
            tests=list(row["tests"]),
            context_files=dict(row.get("context_files", {})),
            relevant_context_files=list(row.get("relevant_context_files", [])),
        )
        for row in rows
    ]


def task_by_id(tasks: list[CodingTask], task_id: str) -> CodingTask:
    for task in tasks:
        if task.task_id == task_id:
            return task
    raise KeyError(f"unknown task_id: {task_id}")
