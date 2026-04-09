from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.io import load_jsonl


@dataclass
class MultiFileBugfixTask:
    task_id: str
    issue: str
    repo_files: dict[str, str]
    execution_order: list[str]
    primary_file: str
    canonical_patch: dict[str, str]
    relevant_patch_files: list[str]
    tests: list[str]


def load_multifile_bugfix_tasks(path: str | Path) -> list[MultiFileBugfixTask]:
    rows = load_jsonl(path)
    return [
        MultiFileBugfixTask(
            task_id=row["task_id"],
            issue=row["issue"],
            repo_files=dict(row["repo_files"]),
            execution_order=list(row["execution_order"]),
            primary_file=row["primary_file"],
            canonical_patch=dict(row["canonical_patch"]),
            relevant_patch_files=list(row["relevant_patch_files"]),
            tests=list(row["tests"]),
        )
        for row in rows
    ]
