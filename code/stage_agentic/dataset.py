from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.io import load_jsonl


@dataclass
class AgentTask:
    task_id: str
    instruction: str
    expected_answer: str
    tool_context: dict


def load_agent_tasks(path: str | Path) -> list[AgentTask]:
    rows = load_jsonl(path)
    return [
        AgentTask(
            task_id=row["task_id"],
            instruction=row["instruction"],
            expected_answer=str(row["expected_answer"]),
            tool_context=dict(row.get("tool_context", {})),
        )
        for row in rows
    ]
