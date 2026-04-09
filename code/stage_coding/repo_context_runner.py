from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_coding.context_builder import PackedContext, pack_retrieved_context
from stage_coding.dataset import CodingTask, load_coding_tasks
from stage_coding.prompt_template import render_prompt


@dataclass
class RepoContextBuildResult:
    task_id: str
    strategy: str
    candidate: str
    selected_context_files: list[str]
    relevant_context_recall: float
    context_char_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_repo_context/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--strategy", choices=["local_only", "contextual", "retrieved", "reference"], default="retrieved")
    parser.add_argument("--show-prompt", action="store_true")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def local_only_solution(task: CodingTask) -> str:
    implementations = {
        "render_priority_summary": (
            "def render_priority_summary(priority: str, title: str) -> str:\n"
            "    return f'{priority}: {title}'"
        ),
        "schedule_retry_ms": (
            "def schedule_retry_ms(base_seconds: int, attempt: int) -> int:\n"
            "    return base_seconds * attempt"
        ),
        "is_escalation_channel": (
            "def is_escalation_channel(name: str) -> bool:\n"
            "    return name.startswith('sev')"
        ),
    }
    return implementations.get(task.task_id, task.starter_code.replace("raise NotImplementedError", "return None"))


def contextual_solution(task: CodingTask) -> str:
    implementations = {
        "render_priority_summary": (
            "def render_priority_summary(priority: str, title: str) -> str:\n"
            "    return f'{PRIORITY_LABELS[priority]}: {title}'"
        ),
        "schedule_retry_ms": (
            "def schedule_retry_ms(base_seconds: int, attempt: int) -> int:\n"
            "    return seconds_to_ms(base_seconds * attempt)"
        ),
        "is_escalation_channel": (
            "def is_escalation_channel(name: str) -> bool:\n"
            "    return normalize_channel(name) in ESCALATION_CHANNELS"
        ),
    }
    return implementations.get(task.task_id, local_only_solution(task))


def build_context(task: CodingTask, strategy: str) -> PackedContext:
    if strategy == "contextual":
        return PackedContext(
            files=dict(task.context_files),
            selected_paths=list(task.context_files),
            relevant_recall=1.0 if task.relevant_context_files else 0.0,
            context_char_count=sum(len(content) for content in task.context_files.values()),
        )
    if strategy == "retrieved":
        return pack_retrieved_context(task)
    return PackedContext(files={}, selected_paths=[], relevant_recall=0.0, context_char_count=0)


def build_candidate(task: CodingTask, strategy: str) -> RepoContextBuildResult:
    if strategy == "reference":
        candidate = task.canonical_solution
        packed_context = build_context(task, "contextual")
    elif strategy == "contextual":
        candidate = contextual_solution(task)
        packed_context = build_context(task, strategy)
    elif strategy == "retrieved":
        packed_context = build_context(task, strategy)
        if packed_context.relevant_recall >= 1.0:
            candidate = contextual_solution(task)
        else:
            candidate = local_only_solution(task)
    else:
        candidate = local_only_solution(task)
        packed_context = build_context(task, strategy)
    return RepoContextBuildResult(
        task_id=task.task_id,
        strategy=strategy,
        candidate=candidate,
        selected_context_files=packed_context.selected_paths,
        relevant_context_recall=packed_context.relevant_recall,
        context_char_count=packed_context.context_char_count,
    )


def main() -> None:
    args = parse_args()
    tasks = load_coding_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        result = build_candidate(task, args.strategy)
        if args.show_prompt:
            print(f"Task: {task.task_id}")
            print(render_prompt(task, build_context(task, args.strategy).files))
        print(f"Task: {task.task_id}")
        print(result.candidate)
        print(f"Selected context: {result.selected_context_files}")
        print(f"Relevant recall: {result.relevant_context_recall:.2f}")
        print("-" * 72)
        rows.append(asdict(result))

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved candidates to {output_path}")


if __name__ == "__main__":
    main()
