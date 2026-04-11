from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from common.io import load_jsonl


@dataclass
class MultimodalTask:
    task_id: str
    asset_path: str
    instruction: str
    expected_answer: str
    visual_context: dict
    expected_fields: dict[str, str] = field(default_factory=dict)
    target_strategy: str = ""


def load_multimodal_tasks(path: str | Path) -> list[MultimodalTask]:
    rows = load_jsonl(path)
    return [
        MultimodalTask(
            task_id=row["task_id"],
            asset_path=row["asset_path"],
            instruction=row["instruction"],
            expected_answer=str(row["expected_answer"]),
            visual_context=dict(row.get("visual_context", {})),
            expected_fields={key: str(value) for key, value in dict(row.get("expected_fields", {})).items()},
            target_strategy=str(row.get("target_strategy", "")),
        )
        for row in rows
    ]
