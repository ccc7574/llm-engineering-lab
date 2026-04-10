from __future__ import annotations

import argparse
import json
import shlex
from datetime import datetime
from pathlib import Path


FAILURE_SIGNALS = ("passed", "success", "pass_at_k_hit", "useful")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-report", default="runs/regression_suite_report.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def load_report(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def failed_items(stdout_excerpt: str) -> list[str]:
    items = []
    for line in stdout_excerpt.splitlines():
        if ": fail" in line:
            items.append(line.split(": fail", 1)[0].strip())
    return items


def sanitize_token(value: str) -> str:
    safe = []
    for char in value:
        if char.isalnum() or char in ("-", "_", "."):
            safe.append(char)
        else:
            safe.append("_")
    return "".join(safe).strip("_") or "item"


def resolve_report_path(suite_report_path: Path, report_path: str) -> Path | None:
    candidate = Path(report_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    if candidate.parts and suite_report_path.parent.name == candidate.parts[0]:
        candidates = [
            suite_report_path.parent.parent / candidate,
            suite_report_path.parent / candidate,
            candidate,
        ]
    else:
        candidates = [
            suite_report_path.parent / candidate,
            candidate,
        ]

    for path in candidates:
        if path.exists():
            return path
    return None


def remove_arg(command: list[str], flag: str) -> list[str]:
    updated: list[str] = []
    skip_next = False
    for token in command:
        if skip_next:
            skip_next = False
            continue
        if token == flag:
            skip_next = True
            continue
        updated.append(token)
    return updated


def replace_or_append_arg(command: list[str], flag: str, value: str) -> list[str]:
    updated = list(command)
    for index, token in enumerate(updated):
        if token == flag:
            if index + 1 < len(updated):
                updated[index + 1] = value
            else:
                updated.append(value)
            return updated
    updated.extend([flag, value])
    return updated


def build_replay_command(command: list[str], step_name: str, task_id: str) -> tuple[list[str], str]:
    replay_report_path = f"runs/replay/{sanitize_token(step_name)}__{sanitize_token(task_id)}.json"
    replay_command = remove_arg(list(command), "--task-id")
    replay_command = replace_or_append_arg(replay_command, "--task-id", task_id)
    replay_command = replace_or_append_arg(replay_command, "--report-path", replay_report_path)
    return replay_command, replay_report_path


def detect_failure_signal(row: dict) -> tuple[str, object] | None:
    for key in FAILURE_SIGNALS:
        if key in row and row.get(key) is False:
            return key, False
    return None


def sample_failure_summary(row: dict, failure_signal: str) -> str | None:
    if row.get("failure_message"):
        return str(row["failure_message"])
    if row.get("failure_type"):
        return str(row["failure_type"])
    if row.get("selected_failure_types"):
        values = row["selected_failure_types"]
        if isinstance(values, list) and values:
            return ",".join(str(value) for value in values)
    if "answer" in row or "expected_answer" in row:
        return f"answer={row.get('answer')} expected={row.get('expected_answer')}"
    if "reference_passes" in row or "buggy_caught" in row:
        return (
            f"reference_passes={row.get('reference_passes')} "
            f"buggy_caught={row.get('buggy_caught')}"
        )
    return f"{failure_signal}=false"


def extract_failed_sample_rows(
    suite_report_path: Path,
    suite_result: dict,
) -> list[dict]:
    rows: list[dict] = []
    command = list(suite_result.get("command", []))
    if not command:
        return rows

    for report_ref in suite_result.get("expected_outputs", []):
        if not str(report_ref).endswith(".json"):
            continue
        resolved_path = resolve_report_path(suite_report_path, str(report_ref))
        if resolved_path is None:
            continue
        try:
            report = load_report(resolved_path)
        except (json.JSONDecodeError, OSError):
            continue

        for result_row in report.get("results", []):
            if not isinstance(result_row, dict):
                continue
            task_id = result_row.get("task_id")
            failure = detect_failure_signal(result_row)
            if not task_id or failure is None:
                continue
            failure_signal, _ = failure
            replay_command, replay_report_path = build_replay_command(
                command,
                suite_result["name"],
                str(task_id),
            )
            rows.append(
                {
                    "name": suite_result["name"],
                    "task_id": str(task_id),
                    "failure_signal": failure_signal,
                    "failure_summary": sample_failure_summary(result_row, failure_signal),
                    "source_report": str(report_ref),
                    "source_report_path": str(resolved_path),
                    "replay_report_path": replay_report_path,
                    "replay_command": shlex.join(replay_command),
                }
            )
    return rows


def markdown_step_section(rows: list[dict]) -> list[str]:
    if not rows:
        return ["## Failed Suite Steps", "", "- No failed suite steps were found in the current report."]

    lines = ["## Failed Suite Steps", "", "| Step | Failure Category | Failed Items | Replay Command |", "| --- | --- | --- | --- |"]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['failure_category'] or '-'} | "
            f"{', '.join(row['failed_items']) or '-'} | `{row['replay_command']}` |"
        )
    return lines


def markdown_sample_section(rows: list[dict]) -> list[str]:
    if not rows:
        return ["## Failed Samples", "", "- No failed samples/tasks were found in replayable eval reports."]

    lines = [
        "## Failed Samples",
        "",
        "| Step | Task ID | Failure Signal | Source Report | Replay Command |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['task_id']} | {row['failure_signal']} | "
            f"{row['source_report']} | `{row['replay_command']}` |"
        )
    return lines


def markdown_plan(step_rows: list[dict], sample_rows: list[dict]) -> str:
    lines = [
        "# Failure Replay Plan",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat()}",
        f"- Failed steps: {len(step_rows)}",
        f"- Failed samples/tasks: {len(sample_rows)}",
    ]
    lines.extend(["", *markdown_step_section(step_rows), "", *markdown_sample_section(sample_rows)])
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    suite_report_path = Path(args.suite_report)
    report = load_report(suite_report_path)
    rows = []
    sample_rows = []
    for result in report.get("results", []):
        sample_rows.extend(extract_failed_sample_rows(suite_report_path, result))
        if result.get("status") == "passed":
            continue
        rows.append(
            {
                "name": result["name"],
                "failure_category": result.get("failure_category"),
                "failure_summary": result.get("failure_summary"),
                "failed_items": failed_items(result.get("stdout_excerpt", "")),
                "missing_outputs": list(result.get("missing_outputs", [])),
                "replay_command": shlex.join(result.get("command", [])),
            }
        )

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "suite_report": str(args.suite_report),
        "failed_step_count": len(rows),
        "failed_sample_count": len(sample_rows),
        "rows": rows,
        "sample_rows": sample_rows,
    }

    print(f"failed_step_count={len(rows)}")
    print(f"failed_sample_count={len(sample_rows)}")
    for row in rows:
        print(
            f"{row['name']}\t{row['failure_category'] or '-'}\t"
            f"{','.join(row['failed_items']) or '-'}\t{row['replay_command']}"
        )
    for row in sample_rows:
        print(
            f"{row['name']}\t{row['task_id']}\t{row['failure_signal']}\t"
            f"{row['replay_command']}"
        )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved failure replay plan to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(markdown_plan(rows, sample_rows), encoding="utf-8")
        print(f"saved failure replay markdown to {md_output_path}")


if __name__ == "__main__":
    main()
