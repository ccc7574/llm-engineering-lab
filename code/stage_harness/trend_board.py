from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-board", default="runs/summary_board.json")
    parser.add_argument("--suite-report", default="runs/regression_suite_report.json")
    parser.add_argument("--baseline-snapshot", default=None)
    parser.add_argument("--snapshot-output", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    parser.add_argument("--top-steps", type=int, default=5)
    parser.add_argument("--top-drifts", type=int, default=8)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_snapshot(summary_board: dict, suite_report: dict, top_steps: int) -> dict:
    suite_rows = list(suite_report.get("results", []))
    slowest_steps = sorted(
        (
            {
                "name": row["name"],
                "status": row["status"],
                "duration_seconds": float(row.get("duration_seconds", 0.0)),
                "attempt_count": int(row.get("attempt_count", 0)),
            }
            for row in suite_rows
        ),
        key=lambda row: row["duration_seconds"],
        reverse=True,
    )[:top_steps]
    track_rows = []
    for row in summary_board.get("rows", []):
        track_rows.append(
            {
                "track_key": row["track_key"],
                "label": row["label"],
                "status": row["status"],
                "primary_metric": row["primary_metric"],
                "quality_delta": float(row["quality_delta"]),
                "cost_signals": {
                    item["metric"]: float(item["delta"])
                    for item in row.get("cost_signals", [])
                },
            }
        )
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "suite": {
            "run_mode": suite_report.get("run_mode"),
            "overall_status": suite_report.get("overall_status"),
            "release_decision": suite_report.get("release_decision"),
            "steps_total": int(suite_report.get("steps_total", 0)),
            "steps_passed": int(suite_report.get("steps_passed", 0)),
            "total_duration_seconds": sum(float(row.get("duration_seconds", 0.0)) for row in suite_rows),
            "slowest_steps": slowest_steps,
        },
        "tracks": track_rows,
    }


def compare_snapshots(current: dict, baseline: dict, top_drifts: int) -> dict:
    current_steps = {
        row["name"]: row for row in current.get("suite", {}).get("slowest_steps", [])
    }
    baseline_steps = {
        row["name"]: row for row in baseline.get("suite", {}).get("slowest_steps", [])
    }
    step_duration_changes = []
    for name in sorted(set(current_steps) | set(baseline_steps)):
        current_duration = float(current_steps.get(name, {}).get("duration_seconds", 0.0))
        baseline_duration = float(baseline_steps.get(name, {}).get("duration_seconds", 0.0))
        delta = current_duration - baseline_duration
        if delta:
            step_duration_changes.append(
                {
                    "name": name,
                    "baseline_duration_seconds": baseline_duration,
                    "current_duration_seconds": current_duration,
                    "delta_seconds": delta,
                }
            )
    step_duration_changes.sort(key=lambda row: abs(row["delta_seconds"]), reverse=True)

    current_tracks = {row["track_key"]: row for row in current.get("tracks", [])}
    baseline_tracks = {row["track_key"]: row for row in baseline.get("tracks", [])}
    track_cost_drifts = []
    quality_delta_changes = []
    for track_key in sorted(set(current_tracks) | set(baseline_tracks)):
        current_row = current_tracks.get(track_key, {})
        baseline_row = baseline_tracks.get(track_key, {})
        current_quality = float(current_row.get("quality_delta", 0.0))
        baseline_quality = float(baseline_row.get("quality_delta", 0.0))
        quality_change = current_quality - baseline_quality
        if quality_change:
            quality_delta_changes.append(
                {
                    "track_key": track_key,
                    "label": current_row.get("label") or baseline_row.get("label") or track_key,
                    "baseline_quality_delta": baseline_quality,
                    "current_quality_delta": current_quality,
                    "delta_change": quality_change,
                }
            )

        current_costs = current_row.get("cost_signals", {})
        baseline_costs = baseline_row.get("cost_signals", {})
        for metric in sorted(set(current_costs) | set(baseline_costs)):
            current_value = float(current_costs.get(metric, 0.0))
            baseline_value = float(baseline_costs.get(metric, 0.0))
            drift = current_value - baseline_value
            if drift:
                track_cost_drifts.append(
                    {
                        "track_key": track_key,
                        "label": current_row.get("label") or baseline_row.get("label") or track_key,
                        "metric": metric,
                        "baseline_delta": baseline_value,
                        "current_delta": current_value,
                        "drift": drift,
                    }
                )

    track_cost_drifts.sort(key=lambda row: abs(row["drift"]), reverse=True)
    quality_delta_changes.sort(key=lambda row: abs(row["delta_change"]), reverse=True)
    return {
        "suite_duration_delta_seconds": float(current["suite"]["total_duration_seconds"])
        - float(baseline.get("suite", {}).get("total_duration_seconds", 0.0)),
        "step_duration_changes": step_duration_changes[:top_drifts],
        "track_cost_drifts": track_cost_drifts[:top_drifts],
        "quality_delta_changes": quality_delta_changes[:top_drifts],
    }


def build_trend_board(
    summary_board: dict,
    suite_report: dict,
    baseline_snapshot: dict | None,
    top_steps: int,
    top_drifts: int,
) -> dict:
    current_snapshot = build_snapshot(summary_board, suite_report, top_steps)
    comparison = None
    if baseline_snapshot:
        comparison = compare_snapshots(current_snapshot, baseline_snapshot, top_drifts)
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "summary_board": str(summary_board.get("runs_dir", "")),
        "suite_report": suite_report.get("manifest"),
        "baseline_snapshot_present": baseline_snapshot is not None,
        "current_snapshot": current_snapshot,
        "comparison": comparison,
    }


def format_markdown(payload: dict) -> str:
    snapshot = payload["current_snapshot"]
    suite = snapshot["suite"]
    lines = [
        "# Harness Trend Board",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Run mode: {suite['run_mode']}",
        f"- Suite status: {suite['overall_status']}",
        f"- Release decision: {suite['release_decision']}",
        f"- Steps passed: {suite['steps_passed']}/{suite['steps_total']}",
        f"- Total suite duration: {suite['total_duration_seconds']:.2f}s",
    ]
    lines.extend(["", "## Slowest Steps", ""])
    for row in suite.get("slowest_steps", []):
        lines.append(
            f"- `{row['name']}`: {row['duration_seconds']:.2f}s | status={row['status']} | attempts={row['attempt_count']}"
        )

    lines.extend(["", "## Track Cost Signals", ""])
    for row in snapshot.get("tracks", []):
        cost_signals = ", ".join(
            f"{metric}={value:+.3f}" for metric, value in sorted(row.get("cost_signals", {}).items())
        ) or "-"
        lines.append(
            f"- `{row['label']}`: status={row['status']} | quality_delta={row['quality_delta']:+.3f} | cost={cost_signals}"
        )

    comparison = payload.get("comparison")
    if comparison:
        lines.extend(["", "## Trend Changes", ""])
        lines.append(f"- Suite duration delta vs baseline: {comparison['suite_duration_delta_seconds']:+.2f}s")
        if comparison.get("step_duration_changes"):
            lines.extend(["", "### Step Duration Drift", ""])
            for row in comparison["step_duration_changes"]:
                lines.append(
                    f"- `{row['name']}`: {row['baseline_duration_seconds']:.2f}s -> {row['current_duration_seconds']:.2f}s "
                    f"({row['delta_seconds']:+.2f}s)"
                )
        if comparison.get("track_cost_drifts"):
            lines.extend(["", "### Cost Drift", ""])
            for row in comparison["track_cost_drifts"]:
                lines.append(
                    f"- `{row['label']}` `{row['metric']}`: {row['baseline_delta']:+.3f} -> {row['current_delta']:+.3f} "
                    f"({row['drift']:+.3f})"
                )
        if comparison.get("quality_delta_changes"):
            lines.extend(["", "### Quality Delta Drift", ""])
            for row in comparison["quality_delta_changes"]:
                lines.append(
                    f"- `{row['label']}`: {row['baseline_quality_delta']:+.3f} -> {row['current_quality_delta']:+.3f} "
                    f"({row['delta_change']:+.3f})"
                )
    else:
        lines.extend(["", "## Trend Changes", "", "- No baseline snapshot provided. Current run was recorded as a fresh trend snapshot."])

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    summary_board = load_json(args.summary_board)
    suite_report = load_json(args.suite_report)
    baseline_snapshot = load_json(args.baseline_snapshot) if args.baseline_snapshot else None
    payload = build_trend_board(
        summary_board=summary_board,
        suite_report=suite_report,
        baseline_snapshot=baseline_snapshot,
        top_steps=args.top_steps,
        top_drifts=args.top_drifts,
    )

    print(f"baseline_snapshot_present={str(payload['baseline_snapshot_present']).lower()}")
    print(f"total_suite_duration_seconds={payload['current_snapshot']['suite']['total_duration_seconds']:.2f}")
    print(f"tracked_rows={len(payload['current_snapshot']['tracks'])}")

    if args.snapshot_output:
        snapshot_path = Path(args.snapshot_output)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            json.dumps(payload["current_snapshot"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"saved trend snapshot to {snapshot_path}")
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved trend board to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_markdown(payload), encoding="utf-8")
        print(f"saved markdown trend board to {md_output_path}")


if __name__ == "__main__":
    main()
