from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-board", default="runs/summary_board.json")
    parser.add_argument("--suite-report", default="runs/regression_suite_report.json")
    parser.add_argument("--digest", default="runs/notification_digest.json")
    parser.add_argument("--review-summary", default="runs/notification_review_summary.json")
    parser.add_argument("--trend-board", default="runs/harness_trend_board.json")
    parser.add_argument("--dispatch-result", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def recommendation(review_summary: dict) -> str:
    if review_summary.get("ship_ready") and review_summary.get("policy_gate_decision") == "ship":
        return "ready"
    if review_summary.get("overall_gate") == "block":
        return "block"
    return "hold"


def build_checklist(review_summary: dict, summary_board: dict, trend_board: dict) -> list[str]:
    items = []
    if review_summary.get("ship_ready"):
        items.append("Release gate is ship-ready.")
    else:
        items.append("Inspect failed steps and release gate before merge or release.")

    if review_summary.get("policy_gate_decision") == "ship":
        items.append("Notification routing policy changes are within the configured boundary.")
    else:
        items.append("Review notification routing policy diff before enabling or widening dispatch.")

    comparison = trend_board.get("comparison") or {}
    if comparison.get("suite_duration_delta_seconds", 0.0) > 0:
        items.append("Check whether suite duration drift is acceptable for the current workflow SLA.")
    else:
        items.append("No suite duration regression is visible in the current trend snapshot.")

    non_green_tracks = [
        row["label"]
        for row in summary_board.get("rows", [])
        if row.get("status") != "passed"
    ]
    if non_green_tracks:
        items.append(f"Review non-green tracks: {', '.join(non_green_tracks)}.")
    else:
        items.append("All tracked capability lines cleared the current promotion threshold.")
    return items


def build_release_note(
    summary_board: dict,
    suite_report: dict,
    digest: dict,
    review_summary: dict,
    trend_board: dict,
    dispatch_result: dict | None,
) -> dict:
    current_snapshot = trend_board.get("current_snapshot", {})
    suite_snapshot = current_snapshot.get("suite", {})
    comparison = trend_board.get("comparison") or {}
    track_rows = summary_board.get("rows", [])
    top_cost_drifts = comparison.get("track_cost_drifts", [])
    top_slowest_steps = suite_snapshot.get("slowest_steps", [])
    release_status = recommendation(review_summary)
    active_scopes = digest.get("active_scopes") or suite_report.get("active_scopes") or []

    title = {
        "ready": "Release Candidate Ready",
        "hold": "Release Candidate Needs Review",
        "block": "Release Candidate Blocked",
    }[release_status]

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "title": title,
        "release_status": release_status,
        "headline": review_summary.get("headline") or digest.get("headline"),
        "suite_status": suite_report.get("overall_status"),
        "release_gate": review_summary.get("overall_gate"),
        "policy_gate": review_summary.get("policy_gate_decision"),
        "dispatch_status": (dispatch_result or {}).get("final_status", "not_run"),
        "event_name": review_summary.get("event_name"),
        "active_scopes": active_scopes,
        "steps_passed": suite_report.get("steps_passed"),
        "steps_total": suite_report.get("steps_total"),
        "failed_steps": review_summary.get("failed_steps", []),
        "reviewer_notes": review_summary.get("reviewer_notes", []),
        "track_statuses": [
            {
                "label": row["label"],
                "status": row["status"],
                "primary_metric": row["primary_metric"],
                "quality_delta": row["quality_delta"],
            }
            for row in track_rows
        ],
        "top_slowest_steps": top_slowest_steps[:5],
        "top_cost_drifts": top_cost_drifts[:5],
        "suite_duration_seconds": suite_snapshot.get("total_duration_seconds"),
        "suite_duration_delta_seconds": comparison.get("suite_duration_delta_seconds"),
        "reviewer_checklist": build_checklist(review_summary, summary_board, trend_board),
    }


def format_markdown(payload: dict) -> str:
    lines = [
        f"# {payload['title']}",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Headline: {payload['headline']}",
        f"- Event: {payload['event_name']}",
        f"- Release status: {payload['release_status']}",
        f"- Suite: {payload['suite_status']} ({payload['steps_passed']}/{payload['steps_total']})",
        f"- Release gate: {payload['release_gate']}",
        f"- Policy gate: {payload['policy_gate']}",
        f"- Dispatch status: {payload['dispatch_status']}",
    ]
    if payload.get("active_scopes"):
        lines.append(f"- Active scopes: {', '.join(payload['active_scopes'])}")
    if payload.get("suite_duration_seconds") is not None:
        lines.append(f"- Suite duration: {float(payload['suite_duration_seconds']):.2f}s")
    if payload.get("suite_duration_delta_seconds") is not None:
        lines.append(f"- Suite duration delta: {float(payload['suite_duration_delta_seconds']):+.2f}s")

    lines.extend(["", "## Reviewer Notes", ""])
    for note in payload.get("reviewer_notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Reviewer Checklist", ""])
    for item in payload.get("reviewer_checklist", []):
        lines.append(f"- {item}")

    if payload.get("failed_steps"):
        lines.extend(["", "## Failed Steps", ""])
        for step in payload["failed_steps"][:8]:
            lines.append(f"- `{step}`")

    lines.extend(["", "## Track Statuses", ""])
    for row in payload.get("track_statuses", []):
        lines.append(
            f"- `{row['label']}`: status={row['status']} | {row['primary_metric']} delta={float(row['quality_delta']):+.3f}"
        )

    if payload.get("top_slowest_steps"):
        lines.extend(["", "## Slowest Steps", ""])
        for row in payload["top_slowest_steps"]:
            lines.append(
                f"- `{row['name']}`: {float(row['duration_seconds']):.2f}s | status={row['status']} | attempts={row['attempt_count']}"
            )

    if payload.get("top_cost_drifts"):
        lines.extend(["", "## Cost Drift", ""])
        for row in payload["top_cost_drifts"]:
            lines.append(
                f"- `{row['label']}` `{row['metric']}`: {float(row['baseline_delta']):+.3f} -> {float(row['current_delta']):+.3f} ({float(row['drift']):+.3f})"
            )

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    summary_board = load_json(args.summary_board)
    suite_report = load_json(args.suite_report)
    digest = load_json(args.digest)
    review_summary = load_json(args.review_summary)
    trend_board = load_json(args.trend_board)
    dispatch_result = load_json(args.dispatch_result) if args.dispatch_result else None
    payload = build_release_note(
        summary_board=summary_board,
        suite_report=suite_report,
        digest=digest,
        review_summary=review_summary,
        trend_board=trend_board,
        dispatch_result=dispatch_result,
    )

    print(f"release_status={payload['release_status']}")
    print(f"dispatch_status={payload['dispatch_status']}")
    print(f"track_rows={len(payload['track_statuses'])}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved release note to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_markdown(payload), encoding="utf-8")
        print(f"saved markdown release note to {md_output_path}")


if __name__ == "__main__":
    main()
