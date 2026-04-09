from __future__ import annotations

from dataclasses import dataclass

from stage_coding.bugfix_dataset import BugfixTask
from stage_coding.execution import evaluate_python_candidate


@dataclass
class JudgeScore:
    passed: bool
    execution_score: float
    issue_alignment_score: float
    total_score: float
    failure_type: str | None


def issue_alignment_score(task: BugfixTask, candidate: str) -> float:
    score = 0.0
    lowered_issue = task.issue.lower()
    lowered_candidate = candidate.lower()

    if "trim" in lowered_issue and ".strip()" in lowered_candidate:
        score += 1.0
    if "lowercase" in lowered_issue and ".lower()" in lowered_candidate:
        score += 1.0
    if "with '#'" in lowered_issue and "#" in candidate:
        score += 1.0
    if "divides by 100" in lowered_issue and "/ 60" in candidate:
        score += 1.0
    return score


def score_bugfix_candidate(task: BugfixTask, candidate: str) -> JudgeScore:
    execution = evaluate_python_candidate(candidate=candidate, tests=task.tests)
    execution_score = 10.0 if execution.passed else -2.0
    alignment = issue_alignment_score(task, candidate)
    return JudgeScore(
        passed=execution.passed,
        execution_score=execution_score,
        issue_alignment_score=alignment,
        total_score=execution_score + alignment,
        failure_type=execution.failure_type,
    )
