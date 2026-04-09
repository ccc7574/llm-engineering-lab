from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir


@dataclass
class SuiteStep:
    name: str
    command: list[str]
    expected_outputs: list[str]
    timeout_seconds: int = 300


@dataclass
class StepResult:
    name: str
    status: str
    command: list[str]
    duration_seconds: float
    return_code: int | None
    expected_outputs: list[str]
    missing_outputs: list[str]
    stdout_excerpt: str
    stderr_excerpt: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="manifests/regression_v2_suite.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-ship", action="store_true")
    return parser.parse_args()


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_steps(payload: dict) -> list[SuiteStep]:
    return [
        SuiteStep(
            name=row["name"],
            command=list(row["command"]),
            expected_outputs=list(row.get("expected_outputs", [])),
            timeout_seconds=int(row.get("timeout_seconds", 300)),
        )
        for row in payload.get("steps", [])
    ]


def excerpt(text: str, max_lines: int = 12) -> str:
    lines = text.strip().splitlines()
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def run_step(step: SuiteStep, repo_root: Path) -> StepResult:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            step.command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=step.timeout_seconds,
            check=False,
        )
        return_code = completed.returncode
        stdout_text = completed.stdout
        stderr_text = completed.stderr
    except subprocess.TimeoutExpired as exc:
        duration_seconds = time.perf_counter() - started
        return StepResult(
            name=step.name,
            status="failed",
            command=step.command,
            duration_seconds=duration_seconds,
            return_code=None,
            expected_outputs=step.expected_outputs,
            missing_outputs=list(step.expected_outputs),
            stdout_excerpt=excerpt(exc.stdout or ""),
            stderr_excerpt=excerpt(exc.stderr or "timeout"),
        )

    missing_outputs = [
        output_path
        for output_path in step.expected_outputs
        if not (repo_root / output_path).exists()
    ]
    status = "passed" if return_code == 0 and not missing_outputs else "failed"
    duration_seconds = time.perf_counter() - started
    return StepResult(
        name=step.name,
        status=status,
        command=step.command,
        duration_seconds=duration_seconds,
        return_code=return_code,
        expected_outputs=step.expected_outputs,
        missing_outputs=missing_outputs,
        stdout_excerpt=excerpt(stdout_text),
        stderr_excerpt=excerpt(stderr_text),
    )


def load_release_decision(repo_root: Path, results: list[StepResult]) -> str | None:
    gate_step_succeeded = any(result.name == "gate_check" and result.status == "passed" for result in results)
    if not gate_step_succeeded:
        return None
    gate_report = repo_root / "runs" / "gate_report.json"
    if not gate_report.exists():
        return None
    payload = json.loads(gate_report.read_text(encoding="utf-8"))
    return payload.get("overall_gate")


def format_md_report(payload: dict) -> str:
    lines = [
        "# Regression Suite Report",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Suite: {payload['suite_name']}",
        f"- Overall status: {payload['overall_status']}",
        f"- Release decision: {payload.get('release_decision') or 'unknown'}",
        f"- Steps passed: {payload['steps_passed']}/{payload['steps_total']}",
        "",
        "| Step | Status | Duration | Return Code | Missing Outputs |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["results"]:
        missing = ", ".join(row["missing_outputs"]) or "-"
        return_code = "-" if row["return_code"] is None else str(row["return_code"])
        lines.append(
            f"| {row['name']} | {row['status']} | {row['duration_seconds']:.2f}s | "
            f"{return_code} | {missing} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    repo_root = Path(__file__).resolve().parents[2]
    manifest = load_manifest(manifest_path)
    steps = parse_steps(manifest)

    results: list[StepResult] = []
    for step in steps:
        result = run_step(step, repo_root)
        results.append(result)
        print(
            f"{step.name}\t{result.status}\t{result.duration_seconds:.2f}s\t"
            f"return_code={result.return_code}"
        )
        if result.missing_outputs:
            print(f"  missing_outputs={result.missing_outputs}")
        if result.status != "passed" and not args.continue_on_error:
            break

    steps_passed = sum(1 for result in results if result.status == "passed")
    overall_status = "passed" if steps_passed == len(steps) else "failed"
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "manifest": str(manifest_path),
        "suite_name": manifest.get("suite_name", manifest_path.stem),
        "description": manifest.get("description", ""),
        "overall_status": overall_status,
        "release_decision": load_release_decision(repo_root, results),
        "steps_total": len(steps),
        "steps_completed": len(results),
        "steps_passed": steps_passed,
        "continue_on_error": args.continue_on_error,
        "results": [asdict(result) for result in results],
    }

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved suite report to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        ensure_dir(md_output_path.parent)
        md_output_path.write_text(format_md_report(payload), encoding="utf-8")
        print(f"saved markdown suite report to {md_output_path}")

    exit_code = 0
    if args.strict and overall_status != "passed":
        exit_code = 1
    if args.require_ship and payload["release_decision"] != "ship":
        exit_code = 2 if exit_code == 0 else exit_code
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
