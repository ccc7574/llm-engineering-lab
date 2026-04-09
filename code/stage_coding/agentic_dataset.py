from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.io import load_jsonl


@dataclass
class AgenticCodingTask:
    task_id: str
    issue: str
    repo_files: dict[str, str]
    execution_order: list[str]
    primary_file: str
    relevant_context_files: list[str]
    relevant_patch_files: list[str]
    single_pass_patch: dict[str, str]
    repair_patch: dict[str, str]
    tests: list[str]


def load_agentic_coding_tasks(path: str | Path) -> list[AgenticCodingTask]:
    rows = load_jsonl(path)
    return [
        AgenticCodingTask(
            task_id=row["task_id"],
            issue=row["issue"],
            repo_files=dict(row["repo_files"]),
            execution_order=list(row["execution_order"]),
            primary_file=row["primary_file"],
            relevant_context_files=list(row["relevant_context_files"]),
            relevant_patch_files=list(row["relevant_patch_files"]),
            single_pass_patch=dict(row["single_pass_patch"]),
            repair_patch=dict(row["repair_patch"]),
            tests=list(row["tests"]),
        )
        for row in rows
    ]
