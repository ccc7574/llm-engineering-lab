from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-report", default="runs/regression_suite_report.json")
    parser.add_argument("--summary-board", default="runs/summary_board.json")
    parser.add_argument("--gate-report", default="runs/gate_report.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_digest(suite_report: dict, summary_board: dict, gate_report: dict) -> dict:
    failed_steps = [row for row in suite_report.get("results", []) if row.get("status") != "passed"]
    failure_counts = Counter(row.get("failure_category") or "unknown" for row in failed_steps)
    regressed_tracks = [row for row in summary_board.get("rows", []) if row.get("status") == "regressed"]
    flat_tracks = [row for row in summary_board.get("rows", []) if row.get("status") == "flat"]

    if gate_report.get("overall_gate") == "block":
        severity = "critical"
    elif gate_report.get("overall_gate") == "hold":
        severity = "warning"
    elif failed_steps:
        severity = "warning"
    else:
        severity = "info"

    headline = {
        "critical": "Regression suite blocked release",
        "warning": "Regression suite needs attention",
        "info": "Regression suite passed",
    }[severity]
    top_failure_category = failure_counts.most_common(1)[0][0] if failure_counts else None

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "severity": severity,
        "headline": headline,
        "overall_gate": gate_report.get("overall_gate"),
        "suite_status": suite_report.get("overall_status"),
        "run_mode": suite_report.get("run_mode"),
        "steps_passed": suite_report.get("steps_passed"),
        "steps_total": suite_report.get("steps_total"),
        "active_scopes": suite_report.get("active_scopes", []),
        "failed_steps": [
            {
                "name": row.get("name"),
                "failure_category": row.get("failure_category"),
                "failure_summary": row.get("failure_summary"),
                "attempt_count": row.get("attempt_count"),
            }
            for row in failed_steps
        ],
        "failure_counts": dict(failure_counts),
        "top_failure_category": top_failure_category,
        "regressed_tracks": [row.get("label") for row in regressed_tracks],
        "flat_tracks": [row.get("label") for row in flat_tracks],
        "ship_ready": gate_report.get("overall_gate") == "ship" and suite_report.get("overall_status") == "passed",
    }


def format_markdown(digest: dict) -> str:
    lines = [
        "# Regression Notification Digest",
        "",
        f"- Generated at: {digest['generated_at']}",
        f"- Headline: {digest['headline']}",
        f"- Severity: {digest['severity']}",
        f"- Suite status: {digest['suite_status']}",
        f"- Gate: {digest['overall_gate']}",
        f"- Run mode: {digest['run_mode']}",
        f"- Steps passed: {digest['steps_passed']}/{digest['steps_total']}",
    ]
    if digest.get("active_scopes"):
        lines.append(f"- Active scopes: {', '.join(digest['active_scopes'])}")
    lines.extend(["", "## Action Summary", ""])
    if digest["ship_ready"]:
        lines.append("- Current suite is ship-ready. Keep monitoring scheduled runs and cost deltas.")
    else:
        lines.append("- Current suite is not ship-ready. Review failed steps and gate decision before merge or release.")

    if digest["failed_steps"]:
        lines.extend(["", "## Failed Steps", ""])
        for row in digest["failed_steps"]:
            lines.append(
                f"- `{row['name']}`: {row['failure_category']} | {row['failure_summary']} | attempts={row['attempt_count']}"
            )

    if digest["failure_counts"]:
        lines.extend(["", "## Failure Counts", ""])
        if digest.get("top_failure_category"):
            lines.append(f"- Top failure category: `{digest['top_failure_category']}`")
        for category, count in sorted(digest["failure_counts"].items()):
            lines.append(f"- `{category}`: {count}")

    if digest["regressed_tracks"] or digest["flat_tracks"]:
        lines.extend(["", "## Track Signals", ""])
        if digest["regressed_tracks"]:
            lines.append(f"- Regressed tracks: {', '.join(digest['regressed_tracks'])}")
        if digest["flat_tracks"]:
            lines.append(f"- Flat tracks: {', '.join(digest['flat_tracks'])}")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    suite_report = load_json(args.suite_report)
    summary_board = load_json(args.summary_board)
    gate_report = load_json(args.gate_report)
    digest = build_digest(suite_report, summary_board, gate_report)

    print(f"headline={digest['headline']}")
    print(f"severity={digest['severity']}")
    print(f"ship_ready={str(digest['ship_ready']).lower()}")
    print(f"failed_steps={len(digest['failed_steps'])}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved digest to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_markdown(digest), encoding="utf-8")
        print(f"saved markdown digest to {md_output_path}")


if __name__ == "__main__":
    main()
