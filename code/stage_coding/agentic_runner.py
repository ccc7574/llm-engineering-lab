from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_coding.agentic_dataset import AgenticCodingTask, load_agentic_coding_tasks
from stage_coding.context_builder import score_context_file, tokenize
from stage_coding.execution import ExecutionResult, evaluate_python_patch


@dataclass
class AgenticCodingRun:
    task_id: str
    strategy: str
    final_patch_files: dict[str, str]
    files_read: list[str]
    repo_reads: int
    test_runs: int
    patch_attempts: int
    repair_attempts: int
    relevant_context_recall: float
    patch_recall: float
    trace: list[str]
    final_failure_type: str | None = None
    final_failure_message: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_agentic_coding/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--strategy", choices=["single_pass", "repair_loop", "reference"], default="repair_loop")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def compute_recall(selected: list[str], relevant: list[str]) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    hits = sum(1 for path in selected if path in relevant_set)
    return hits / len(relevant_set)


def rank_followup_files(task: AgenticCodingTask, query: str, exclude: set[str]) -> list[str]:
    query_terms = tokenize(query)
    ranked = sorted(
        task.repo_files.items(),
        key=lambda item: score_context_file(query_terms, item[0], item[1]),
        reverse=True,
    )
    return [path for path, _content in ranked if path not in exclude]


def execution_status(execution: ExecutionResult) -> str:
    if execution.passed:
        return "pass"
    return f"fail:{execution.failure_type}"


def run_single_pass(task: AgenticCodingTask) -> AgenticCodingRun:
    files_read = [task.primary_file]
    final_patch_files = dict(task.single_pass_patch)
    trace = [
        f"read_file({task.primary_file})",
        "draft_patch(single_pass)",
        f"submit_patch({sorted(final_patch_files)})",
    ]
    return AgenticCodingRun(
        task_id=task.task_id,
        strategy="single_pass",
        final_patch_files=final_patch_files,
        files_read=files_read,
        repo_reads=len(files_read),
        test_runs=0,
        patch_attempts=1,
        repair_attempts=0,
        relevant_context_recall=compute_recall(files_read, task.relevant_context_files),
        patch_recall=compute_recall(sorted(final_patch_files), task.relevant_patch_files),
        trace=trace,
    )


def run_reference(task: AgenticCodingTask) -> AgenticCodingRun:
    files_read = list(task.relevant_context_files)
    final_patch_files = dict(task.repair_patch)
    return AgenticCodingRun(
        task_id=task.task_id,
        strategy="reference",
        final_patch_files=final_patch_files,
        files_read=files_read,
        repo_reads=len(files_read),
        test_runs=1,
        patch_attempts=1,
        repair_attempts=0,
        relevant_context_recall=compute_recall(files_read, task.relevant_context_files),
        patch_recall=compute_recall(sorted(final_patch_files), task.relevant_patch_files),
        trace=["reference patch"],
    )


def run_repair_loop(task: AgenticCodingTask) -> AgenticCodingRun:
    files_read = [task.primary_file]
    trace = [f"read_file({task.primary_file})", "draft_patch(single_pass)"]
    final_patch_files = dict(task.single_pass_patch)
    patch_attempts = 1
    test_runs = 1
    execution = evaluate_python_patch(
        repo_files=task.repo_files,
        patch_files=final_patch_files,
        tests=task.tests,
        execution_order=task.execution_order,
    )
    trace.append(f"run_tests -> {execution_status(execution)}")

    repair_attempts = 0
    if not execution.passed:
        repair_attempts = 1
        query = "\n".join([task.issue, execution.failure_message or ""])
        for path in rank_followup_files(task, query, exclude=set(files_read)):
            files_read.append(path)
            trace.append(f"read_file({path})")
            if path in task.relevant_context_files:
                break
        trace.append("repair_patch(from_test_feedback)")
        final_patch_files = dict(task.repair_patch)
        patch_attempts += 1
        test_runs += 1
        execution = evaluate_python_patch(
            repo_files=task.repo_files,
            patch_files=final_patch_files,
            tests=task.tests,
            execution_order=task.execution_order,
        )
        trace.append(f"run_tests -> {execution_status(execution)}")

    return AgenticCodingRun(
        task_id=task.task_id,
        strategy="repair_loop",
        final_patch_files=final_patch_files,
        files_read=files_read,
        repo_reads=len(files_read),
        test_runs=test_runs,
        patch_attempts=patch_attempts,
        repair_attempts=repair_attempts,
        relevant_context_recall=compute_recall(files_read, task.relevant_context_files),
        patch_recall=compute_recall(sorted(final_patch_files), task.relevant_patch_files),
        trace=trace,
        final_failure_type=execution.failure_type,
        final_failure_message=execution.failure_message,
    )


def build_run(task: AgenticCodingTask, strategy: str) -> AgenticCodingRun:
    if strategy == "reference":
        return run_reference(task)
    if strategy == "repair_loop":
        return run_repair_loop(task)
    return run_single_pass(task)


def main() -> None:
    args = parse_args()
    tasks = load_agentic_coding_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        run = build_run(task, args.strategy)
        print(f"Task: {task.task_id}")
        print(f"Files read: {run.files_read}")
        print(f"Repo reads: {run.repo_reads}")
        print(f"Test runs: {run.test_runs}")
        print(f"Patch attempts: {run.patch_attempts}")
        print(f"Repair attempts: {run.repair_attempts}")
        print(f"Relevant context recall: {run.relevant_context_recall:.2f}")
        print(f"Patch recall: {run.patch_recall:.2f}")
        for step in run.trace:
            print(f"  {step}")
        if run.final_failure_type:
            print(f"Final failure: {run.final_failure_type} | {run.final_failure_message}")
        print("-" * 72)
        rows.append(asdict(run))

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved agentic coding runs to {output_path}")


if __name__ == "__main__":
    main()
