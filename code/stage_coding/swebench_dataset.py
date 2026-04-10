from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.io import load_jsonl


@dataclass
class SwebenchLiteTask:
    task_id: str
    issue: str
    failing_test_output: str
    repo_files: dict[str, str]
    execution_order: list[str]
    primary_file: str
    relevant_context_files: list[str]
    relevant_patch_files: list[str]
    issue_localized_patch: dict[str, str]
    triage_patch: dict[str, str]
    tests: list[str]


def load_swebench_lite_tasks(path: str | Path) -> list[SwebenchLiteTask]:
    rows = load_jsonl(path)
    return [
        SwebenchLiteTask(
            task_id=row["task_id"],
            issue=row["issue"],
            failing_test_output=row["failing_test_output"],
            repo_files=dict(row["repo_files"]),
            execution_order=list(row["execution_order"]),
            primary_file=row["primary_file"],
            relevant_context_files=list(row["relevant_context_files"]),
            relevant_patch_files=list(row["relevant_patch_files"]),
            issue_localized_patch=dict(row["issue_localized_patch"]),
            triage_patch=dict(row["triage_patch"]),
            tests=list(row["tests"]),
        )
        for row in rows
    ]
