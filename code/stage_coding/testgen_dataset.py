from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.io import load_jsonl


@dataclass
class TestGenTask:
    task_id: str
    instruction: str
    reference_code: str
    buggy_code: str
    tests_should_include: list[str]


def load_testgen_tasks(path: str | Path) -> list[TestGenTask]:
    rows = load_jsonl(path)
    return [
        TestGenTask(
            task_id=row["task_id"],
            instruction=row["instruction"],
            reference_code=row["reference_code"],
            buggy_code=row["buggy_code"],
            tests_should_include=list(row["tests_should_include"]),
        )
        for row in rows
    ]
