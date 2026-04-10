from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.io import load_jsonl


@dataclass
class PassKCandidate:
    sample_id: str
    candidate: str


@dataclass
class PassKTask:
    task_id: str
    instruction: str
    starter_code: str
    entry_point: str
    tests: list[str]
    candidates: list[PassKCandidate]


def load_passk_tasks(path: str | Path) -> list[PassKTask]:
    rows = load_jsonl(path)
    return [
        PassKTask(
            task_id=row["task_id"],
            instruction=row["instruction"],
            starter_code=row["starter_code"],
            entry_point=row["entry_point"],
            tests=list(row["tests"]),
            candidates=[
                PassKCandidate(sample_id=item["sample_id"], candidate=item["candidate"])
                for item in row["candidates"]
            ],
        )
        for row in rows
    ]
