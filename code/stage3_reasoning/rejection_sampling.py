from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path

from common.io import load_jsonl, write_json, write_jsonl
from stage2_sft.dataset import REASONING_INSTRUCTION
from stage3_reasoning.self_consistency import normalize_answer


@dataclass
class RejectionCandidate:
    text: str
    final_answer: str
    verifier_score: float
    passes_numeric_check: bool
    generated_tokens: int


@dataclass
class RejectionTask:
    task_id: str
    question: str
    expected_answer: str
    candidates: list[RejectionCandidate]


@dataclass
class SelectionResult:
    task_id: str
    strategy: str
    accepted: bool
    answer: str
    expected_answer: str
    success: bool
    verifier_score: float
    sampled_candidates: int
    accepted_candidates: int
    rejected_candidates: int
    trace: list[str]
    selected_text: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_reasoning_rejection/eval.jsonl")
    parser.add_argument("--strategy", choices=["consensus", "rejection_sampling"], default="rejection_sampling")
    parser.add_argument("--min-verifier-score", type=float, default=0.85)
    parser.add_argument("--output", default=None)
    parser.add_argument("--accepted-output", default=None)
    return parser.parse_args()


def load_rejection_tasks(path: str | Path) -> list[RejectionTask]:
    rows = load_jsonl(path)
    tasks = []
    for row in rows:
        tasks.append(
            RejectionTask(
                task_id=str(row["task_id"]),
                question=str(row["question"]),
                expected_answer=str(row["expected_answer"]),
                candidates=[
                    RejectionCandidate(
                        text=str(candidate["text"]),
                        final_answer=str(candidate.get("final_answer", "")),
                        verifier_score=float(candidate.get("verifier_score", 0.0)),
                        passes_numeric_check=bool(candidate.get("passes_numeric_check", False)),
                        generated_tokens=int(candidate.get("generated_tokens", 0)),
                    )
                    for candidate in row.get("candidates", [])
                ],
            )
        )
    return tasks


def rendered_output(candidate: RejectionCandidate) -> str:
    text = candidate.text.strip()
    if candidate.final_answer and "Final Answer:" not in text:
        if text:
            return f"{text}\nFinal Answer: {candidate.final_answer}"
        return f"Final Answer: {candidate.final_answer}"
    return text


def consensus_select(task: RejectionTask) -> SelectionResult:
    counts: dict[str, int] = {}
    representative: dict[str, RejectionCandidate] = {}
    for candidate in task.candidates:
        key = normalize_answer(candidate.final_answer)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
        representative.setdefault(key, candidate)

    trace = [f"parsed_candidates -> {len(counts)} unique answers"]
    if not counts:
        return SelectionResult(
            task_id=task.task_id,
            strategy="consensus",
            accepted=False,
            answer="",
            expected_answer=task.expected_answer,
            success=False,
            verifier_score=0.0,
            sampled_candidates=len(task.candidates),
            accepted_candidates=0,
            rejected_candidates=len(task.candidates),
            trace=trace + ["consensus -> no parsed candidates"],
        )

    best_key, support = max(
        counts.items(),
        key=lambda item: (
            item[1],
            -representative[item[0]].generated_tokens,
            representative[item[0]].verifier_score,
        ),
    )
    selected = representative[best_key]
    success = best_key == normalize_answer(task.expected_answer)
    return SelectionResult(
        task_id=task.task_id,
        strategy="consensus",
        accepted=True,
        answer=selected.final_answer,
        expected_answer=task.expected_answer,
        success=success,
        verifier_score=selected.verifier_score,
        sampled_candidates=len(task.candidates),
        accepted_candidates=support,
        rejected_candidates=max(len(task.candidates) - support, 0),
        trace=trace + [f"consensus -> answer={selected.final_answer} support={support}"],
        selected_text=rendered_output(selected),
    )


def rejection_sampling_select(task: RejectionTask, min_verifier_score: float) -> SelectionResult:
    accepted_candidates = [
        candidate
        for candidate in task.candidates
        if candidate.final_answer
        and candidate.passes_numeric_check
        and candidate.verifier_score >= min_verifier_score
    ]
    trace = [
        f"sampled_candidates -> {len(task.candidates)}",
        f"filter.parsed_and_numeric_and_score>={min_verifier_score:.2f} -> {len(accepted_candidates)}",
    ]
    if not accepted_candidates:
        return SelectionResult(
            task_id=task.task_id,
            strategy="rejection_sampling",
            accepted=False,
            answer="",
            expected_answer=task.expected_answer,
            success=False,
            verifier_score=0.0,
            sampled_candidates=len(task.candidates),
            accepted_candidates=0,
            rejected_candidates=len(task.candidates),
            trace=trace + ["reject_prompt -> no candidate passed filter"],
        )

    selected = max(
        accepted_candidates,
        key=lambda candidate: (candidate.verifier_score, -candidate.generated_tokens),
    )
    success = normalize_answer(selected.final_answer) == normalize_answer(task.expected_answer)
    return SelectionResult(
        task_id=task.task_id,
        strategy="rejection_sampling",
        accepted=True,
        answer=selected.final_answer,
        expected_answer=task.expected_answer,
        success=success,
        verifier_score=selected.verifier_score,
        sampled_candidates=len(task.candidates),
        accepted_candidates=len(accepted_candidates),
        rejected_candidates=len(task.candidates) - len(accepted_candidates),
        trace=trace + [f"select_highest_score -> answer={selected.final_answer} score={selected.verifier_score:.3f}"],
        selected_text=rendered_output(selected),
    )


def build_training_rows(tasks: list[RejectionTask], results: list[SelectionResult]) -> list[dict]:
    task_by_id = {task.task_id: task for task in tasks}
    rows = []
    for result in results:
        if not result.accepted or not result.selected_text:
            continue
        task = task_by_id[result.task_id]
        rows.append(
            {
                "instruction": REASONING_INSTRUCTION,
                "input": task.question,
                "output": result.selected_text,
                "source_task_id": result.task_id,
                "selection_strategy": result.strategy,
                "verifier_score": result.verifier_score,
            }
        )
    return rows


def run_selection(tasks: list[RejectionTask], strategy: str, min_verifier_score: float) -> list[SelectionResult]:
    if strategy == "consensus":
        return [consensus_select(task) for task in tasks]
    return [rejection_sampling_select(task, min_verifier_score) for task in tasks]


def main() -> None:
    args = parse_args()
    tasks = load_rejection_tasks(args.data_path)
    results = run_selection(tasks, args.strategy, args.min_verifier_score)

    for result in results:
        status = "accepted" if result.accepted else "rejected"
        print(f"{result.task_id}: {status} answer={result.answer or '[none]'} expected={result.expected_answer}")
        for step in result.trace:
            print(f"  {step}")

    if args.output:
        write_json(args.output, {"results": [asdict(result) for result in results]})
        print(f"saved rejection sampling report to {args.output}")
    if args.accepted_output:
        write_jsonl(args.accepted_output, build_training_rows(tasks, results))
        print(f"saved accepted dataset to {args.accepted_output}")


if __name__ == "__main__":
    main()
