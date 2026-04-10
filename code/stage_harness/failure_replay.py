from __future__ import annotations

import argparse
import json
import shlex
from datetime import datetime
from pathlib import Path


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


def markdown_plan(rows: list[dict]) -> str:
    lines = [
        "# Failure Replay Plan",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat()}",
        f"- Failed steps: {len(rows)}",
    ]
    if not rows:
        lines.extend(["", "- No failed suite steps were found in the current report."])
        return "\n".join(lines) + "\n"

    lines.extend(["", "| Step | Failure Category | Failed Items | Replay Command |", "| --- | --- | --- | --- |"])
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['failure_category'] or '-'} | "
            f"{', '.join(row['failed_items']) or '-'} | `{row['replay_command']}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    report = load_report(args.suite_report)
    rows = []
    for result in report.get("results", []):
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
        "rows": rows,
    }

    print(f"failed_step_count={len(rows)}")
    for row in rows:
        print(
            f"{row['name']}\t{row['failure_category'] or '-'}\t"
            f"{','.join(row['failed_items']) or '-'}\t{row['replay_command']}"
        )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved failure replay plan to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(markdown_plan(rows), encoding="utf-8")
        print(f"saved failure replay markdown to {md_output_path}")


if __name__ == "__main__":
    main()
