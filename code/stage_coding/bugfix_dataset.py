from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.io import load_jsonl


@dataclass
class BugfixTask:
    task_id: str
    issue: str
    buggy_code: str
    entry_point: str
    canonical_fix: str
    tests: list[str]


def load_bugfix_tasks(path: str | Path) -> list[BugfixTask]:
    rows = load_jsonl(path)
    return [
        BugfixTask(
            task_id=row["task_id"],
            issue=row["issue"],
            buggy_code=row["buggy_code"],
            entry_point=row["entry_point"],
            canonical_fix=row["canonical_fix"],
            tests=list(row["tests"]),
        )
        for row in rows
    ]
