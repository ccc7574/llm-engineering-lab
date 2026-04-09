from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_coding.multifile_bugfix_dataset import MultiFileBugfixTask, load_multifile_bugfix_tasks


@dataclass
class PatchCandidate:
    task_id: str
    strategy: str
    patch_files: dict[str, str]
    touched_files: list[str]
    patch_recall: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_multifile_bugfix/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--strategy", choices=["single_file", "patch_protocol", "reference"], default="patch_protocol")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def single_file_patch(task: MultiFileBugfixTask) -> dict[str, str]:
    patches = {
        "retry_plan_multifile": {
            "planner.py": (
                "def build_retry_plan(base_seconds: int, attempts: int) -> list[int]:\n"
                "    return [seconds_to_ms(base_seconds * attempt) for attempt in range(1, attempts + 1)]"
            )
        },
        "alert_render_multifile": {
            "alerts.py": (
                "def render_alert(service: str, severity: str) -> str:\n"
                "    return f\"{normalize_service(service)}:{SEVERITY_LABELS[severity]}\""
            )
        },
        "route_key_multifile": {
            "keys.py": (
                "def build_route_key(team: str, incident_id: int) -> str:\n"
                "    return f\"{route_prefix(team)}#{incident_id}\""
            )
        },
    }
    return patches.get(task.task_id, {})


def patch_protocol_patch(task: MultiFileBugfixTask) -> dict[str, str]:
    patches = {
        "retry_plan_multifile": {
            "retry_utils.py": (
                "def seconds_to_ms(seconds: int) -> int:\n"
                "    return seconds * 1000"
            ),
            "planner.py": (
                "def build_retry_plan(base_seconds: int, attempts: int) -> list[int]:\n"
                "    return [seconds_to_ms(base_seconds * attempt) for attempt in range(1, attempts + 1)]"
            ),
        },
        "alert_render_multifile": {
            "formatting.py": (
                "def normalize_service(name: str) -> str:\n"
                "    return name.strip().lower()"
            ),
            "alerts.py": (
                "def render_alert(service: str, severity: str) -> str:\n"
                "    return f\"{normalize_service(service)}:{SEVERITY_LABELS[severity]}\""
            ),
        },
        "route_key_multifile": {
            "routes.py": (
                "def route_prefix(team: str) -> str:\n"
                "    return team.strip().lower()"
            ),
            "keys.py": (
                "def build_route_key(team: str, incident_id: int) -> str:\n"
                "    return f\"{route_prefix(team)}#{incident_id}\""
            ),
        },
    }
    return patches.get(task.task_id, {})


def build_patch_candidate(task: MultiFileBugfixTask, strategy: str) -> PatchCandidate:
    if strategy == "reference":
        patch_files = dict(task.canonical_patch)
    elif strategy == "patch_protocol":
        patch_files = patch_protocol_patch(task)
    else:
        patch_files = single_file_patch(task)

    touched_files = sorted(patch_files)
    relevant = set(task.relevant_patch_files)
    patch_recall = sum(1 for path in touched_files if path in relevant) / max(len(relevant), 1)
    return PatchCandidate(
        task_id=task.task_id,
        strategy=strategy,
        patch_files=patch_files,
        touched_files=touched_files,
        patch_recall=patch_recall,
    )


def main() -> None:
    args = parse_args()
    tasks = load_multifile_bugfix_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        candidate = build_patch_candidate(task, args.strategy)
        print(f"Task: {task.task_id}")
        print(f"Touched files: {candidate.touched_files}")
        print(f"Patch recall: {candidate.patch_recall:.2f}")
        for path, content in candidate.patch_files.items():
            print(f"[{path}]")
            print(content)
        print("-" * 72)
        rows.append(asdict(candidate))

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved patch candidates to {output_path}")


if __name__ == "__main__":
    main()
