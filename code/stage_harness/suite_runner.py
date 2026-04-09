from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir


META_STEP_NAMES = {"run_registry", "summary_board", "gate_check"}


@dataclass
class SuiteStep:
    name: str
    command: list[str]
    expected_outputs: list[str]
    timeout_seconds: int = 300
    retries: int = 0
    retry_delay_seconds: float = 0.0
    scope_tags: list[str] = field(default_factory=list)
    always_run: bool = False


@dataclass
class StepResult:
    name: str
    status: str
    command: list[str]
    duration_seconds: float
    return_code: int | None
    attempt_count: int
    failure_category: str | None
    failure_summary: str | None
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
    parser.add_argument("--changed-files-path", default=None)
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--clean-regression-artifacts", action="store_true")
    return parser.parse_args()


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def infer_scope_tags(step_name: str) -> list[str]:
    if step_name.startswith(
        (
            "coding_",
            "repo_context_",
            "bugfix_",
            "multifile_bugfix_",
            "testgen_",
            "agentic_coding_",
        )
    ):
        return ["coding"]
    if step_name.startswith("agentic_"):
        return ["agentic"]
    if step_name.startswith("multimodal_"):
        return ["multimodal"]
    if step_name in META_STEP_NAMES:
        return ["harness"]
    return []


def parse_steps(payload: dict) -> list[SuiteStep]:
    default_step_retries = int(payload.get("default_step_retries", 0))
    default_retry_delay_seconds = float(payload.get("default_retry_delay_seconds", 0.0))
    steps = []
    for row in payload.get("steps", []):
        steps.append(
            SuiteStep(
                name=row["name"],
                command=list(row["command"]),
                expected_outputs=list(row.get("expected_outputs", [])),
                timeout_seconds=int(row.get("timeout_seconds", 300)),
                retries=int(row.get("retries", default_step_retries)),
                retry_delay_seconds=float(row.get("retry_delay_seconds", default_retry_delay_seconds)),
                scope_tags=list(row.get("scope_tags", infer_scope_tags(row["name"]))),
                always_run=bool(row.get("always_run", row["name"] in META_STEP_NAMES)),
            )
        )
    return steps


def excerpt(text: str, max_lines: int = 12) -> str:
    lines = text.strip().splitlines()
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def classify_failure(
    return_code: int | None,
    missing_outputs: list[str],
    stdout_excerpt: str,
    stderr_excerpt: str,
) -> tuple[str | None, str | None]:
    if return_code == 0 and not missing_outputs:
        return None, None
    if return_code is None:
        return "timeout", "step timed out before producing expected outputs"
    if missing_outputs:
        return "artifact_missing", f"missing expected outputs: {', '.join(missing_outputs)}"
    combined = "\n".join(part for part in [stderr_excerpt, stdout_excerpt] if part).lower()
    if "syntax_error" in combined or "syntaxerror" in combined:
        return "syntax_error", "command output contains syntax error"
    if "assertion_failed" in combined or "assert " in combined:
        return "test_failure", "tests failed on candidate output"
    if "module not found" in combined or "modulenotfounderror" in combined or "importerror" in combined:
        return "dependency_error", "missing import or dependency during step execution"
    if return_code != 0:
        return "process_error", f"command exited with non-zero status {return_code}"
    return "unknown_failure", "step failed for an uncategorized reason"


def execute_step_once(step: SuiteStep, repo_root: Path) -> tuple[int | None, list[str], str, str, float]:
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
        missing_outputs = [
            output_path
            for output_path in step.expected_outputs
            if not (repo_root / output_path).exists()
        ]
    except subprocess.TimeoutExpired as exc:
        return_code = None
        stdout_text = exc.stdout or ""
        stderr_text = exc.stderr or "timeout"
        missing_outputs = list(step.expected_outputs)
    duration_seconds = time.perf_counter() - started
    return return_code, missing_outputs, stdout_text, stderr_text, duration_seconds


def run_step(step: SuiteStep, repo_root: Path) -> StepResult:
    total_duration = 0.0
    final_return_code: int | None = None
    final_missing_outputs: list[str] = []
    final_stdout_excerpt = ""
    final_stderr_excerpt = ""

    for attempt in range(1, step.retries + 2):
        return_code, missing_outputs, stdout_text, stderr_text, duration_seconds = execute_step_once(step, repo_root)
        total_duration += duration_seconds
        final_return_code = return_code
        final_missing_outputs = missing_outputs
        final_stdout_excerpt = excerpt(stdout_text)
        final_stderr_excerpt = excerpt(stderr_text)
        passed = return_code == 0 and not missing_outputs
        failure_category, failure_summary = classify_failure(
            return_code=return_code,
            missing_outputs=missing_outputs,
            stdout_excerpt=final_stdout_excerpt,
            stderr_excerpt=final_stderr_excerpt,
        )
        if passed or attempt == step.retries + 1:
            return StepResult(
                name=step.name,
                status="passed" if passed else "failed",
                command=step.command,
                duration_seconds=total_duration,
                return_code=final_return_code,
                attempt_count=attempt,
                failure_category=failure_category,
                failure_summary=failure_summary,
                expected_outputs=step.expected_outputs,
                missing_outputs=final_missing_outputs,
                stdout_excerpt=final_stdout_excerpt,
                stderr_excerpt=final_stderr_excerpt,
            )
        if step.retry_delay_seconds > 0:
            time.sleep(step.retry_delay_seconds)

    raise RuntimeError("unreachable")


def load_changed_files(args: argparse.Namespace) -> list[str]:
    changed_files = list(args.changed_file)
    if args.changed_files_path:
        changed_files.extend(
            line.strip()
            for line in Path(args.changed_files_path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    return sorted(set(changed_files))


def find_active_scopes(manifest: dict, changed_files: list[str]) -> list[str]:
    scopes = manifest.get("scopes", {})
    if not changed_files or not scopes:
        return []

    active_scopes = []
    for scope_name, patterns in scopes.items():
        for changed_file in changed_files:
            if any(fnmatch.fnmatch(changed_file, pattern) for pattern in patterns):
                active_scopes.append(scope_name)
                break
    return sorted(set(active_scopes))


def select_steps(steps: list[SuiteStep], active_scopes: list[str], run_all: bool) -> list[SuiteStep]:
    if run_all or not active_scopes:
        return list(steps) if run_all else [step for step in steps if step.always_run]
    active_scope_set = set(active_scopes)
    return [
        step
        for step in steps
        if step.always_run or bool(active_scope_set & set(step.scope_tags))
    ]


def should_run_full_suite(manifest: dict, active_scopes: list[str]) -> bool:
    run_all_scopes = set(manifest.get("run_all_scopes", []))
    return bool(run_all_scopes & set(active_scopes))


def clean_regression_artifacts(repo_root: Path, steps: list[SuiteStep]) -> None:
    cleanup_patterns = [
        "runs/*_regression_diff.json",
        "runs/summary_board.json",
        "runs/summary_board.md",
        "runs/gate_report.json",
        "runs/run_registry.json",
        "runs/regression_suite_report.json",
        "runs/regression_suite_report.md",
    ]
    cleanup_paths = {repo_root / output_path for step in steps for output_path in step.expected_outputs}
    for pattern in cleanup_patterns:
        cleanup_paths.update(repo_root.glob(pattern))
    for path in cleanup_paths:
        if path.exists() and path.is_file():
            path.unlink()


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
        f"- Run mode: {payload['run_mode']}",
        f"- Overall status: {payload['overall_status']}",
        f"- Release decision: {payload.get('release_decision') or 'unknown'}",
        f"- Steps passed: {payload['steps_passed']}/{payload['steps_total']}",
    ]
    if payload.get("active_scopes"):
        lines.append(f"- Active scopes: {', '.join(payload['active_scopes'])}")
    if payload.get("changed_files"):
        lines.append(f"- Changed files: {len(payload['changed_files'])}")
    lines.extend(
        [
            "",
            "| Step | Status | Attempts | Duration | Return Code | Failure Category | Missing Outputs |",
            "| --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in payload["results"]:
        missing = ", ".join(row["missing_outputs"]) or "-"
        return_code = "-" if row["return_code"] is None else str(row["return_code"])
        failure_category = row["failure_category"] or "-"
        lines.append(
            f"| {row['name']} | {row['status']} | {row['attempt_count']} | {row['duration_seconds']:.2f}s | "
            f"{return_code} | {failure_category} | {missing} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    repo_root = Path(__file__).resolve().parents[2]
    manifest = load_manifest(manifest_path)
    steps = parse_steps(manifest)
    changed_files = load_changed_files(args)

    if changed_files:
        active_scopes = find_active_scopes(manifest, changed_files)
        run_all = should_run_full_suite(manifest, active_scopes)
        selected_steps = select_steps(steps, active_scopes, run_all)
        run_mode = "changed_scoped_full" if run_all else "changed_scoped"
    else:
        active_scopes = []
        run_all = True
        selected_steps = list(steps)
        run_mode = "full"

    if args.clean_regression_artifacts:
        clean_regression_artifacts(repo_root, selected_steps)

    results: list[StepResult] = []
    for step in selected_steps:
        result = run_step(step, repo_root)
        results.append(result)
        print(
            f"{step.name}\t{result.status}\t{result.duration_seconds:.2f}s\t"
            f"attempts={result.attempt_count}\treturn_code={result.return_code}"
        )
        if result.missing_outputs:
            print(f"  missing_outputs={result.missing_outputs}")
        if result.status != "passed" and not args.continue_on_error:
            break

    steps_passed = sum(1 for result in results if result.status == "passed")
    steps_total = len(selected_steps)
    overall_status = "passed" if steps_passed == steps_total else "failed"
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "manifest": str(manifest_path),
        "suite_name": manifest.get("suite_name", manifest_path.stem),
        "description": manifest.get("description", ""),
        "run_mode": run_mode,
        "changed_files": changed_files,
        "active_scopes": active_scopes,
        "overall_status": overall_status,
        "release_decision": load_release_decision(repo_root, results),
        "steps_total": steps_total,
        "steps_completed": len(results),
        "steps_passed": steps_passed,
        "continue_on_error": args.continue_on_error,
        "selected_steps": [step.name for step in selected_steps],
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
