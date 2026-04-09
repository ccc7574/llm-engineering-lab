from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import ensure_dir
from stage_agentic.dataset import load_agent_tasks
from stage_agentic.task_runner import build_run


@dataclass
class AgentEvalResult:
    task_id: str
    strategy: str
    answer: str
    expected_answer: str
    success: bool
    tool_calls: int
    steps: int
    state_reads: int
    state_writes: int
    recovery_attempts: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_agentic/eval.jsonl")
    parser.add_argument("--strategy", choices=["direct", "tool_use", "stateful", "reference"], default="tool_use")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def normalize(text: str) -> str:
    return text.strip().lower()


def main() -> None:
    args = parse_args()
    tasks = load_agent_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    results = []
    for task in tasks:
        run = build_run(task, args.strategy)
        success = normalize(run.answer) == normalize(task.expected_answer)
        result = AgentEvalResult(
            task_id=task.task_id,
            strategy=args.strategy,
            answer=run.answer,
            expected_answer=task.expected_answer,
            success=success,
            tool_calls=run.tool_calls,
            steps=run.steps,
            state_reads=run.state_reads,
            state_writes=run.state_writes,
            recovery_attempts=run.recovery_attempts,
        )
        results.append(result)
        status = "pass" if success else "fail"
        print(f"{task.task_id}: {status}")
        print(f"  answer={run.answer}")
        print(f"  expected={task.expected_answer}")
        print(
            f"  tool_calls={run.tool_calls} steps={run.steps} "
            f"state_reads={run.state_reads} state_writes={run.state_writes} "
            f"recovery_attempts={run.recovery_attempts}"
        )

    successes = sum(1 for result in results if result.success)
    total = max(len(results), 1)
    summary = {
        "strategy": args.strategy,
        "task_success_rate": successes / total,
        "successes": successes,
        "total": len(results),
        "avg_tool_calls": sum(result.tool_calls for result in results) / total,
        "avg_steps": sum(result.steps for result in results) / total,
        "avg_state_reads": sum(result.state_reads for result in results) / total,
        "avg_state_writes": sum(result.state_writes for result in results) / total,
        "avg_recovery_attempts": sum(result.recovery_attempts for result in results) / total,
        "results": [asdict(result) for result in results],
    }
    print(f"task_success_rate={summary['task_success_rate']:.3f} ({successes}/{len(results)})")
    print(f"avg_tool_calls={summary['avg_tool_calls']:.2f}")
    print(f"avg_steps={summary['avg_steps']:.2f}")
    print(f"avg_state_reads={summary['avg_state_reads']:.2f}")
    print(f"avg_state_writes={summary['avg_state_writes']:.2f}")
    print(f"avg_recovery_attempts={summary['avg_recovery_attempts']:.2f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
