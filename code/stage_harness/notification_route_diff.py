from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def load_rows(path: str | Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(payload.get("rows", []))


def row_key(row: dict) -> tuple[str, str, str]:
    return row["event_name"], row["severity"], row["gate"]


def compare_rows(baseline_rows: list[dict], candidate_rows: list[dict]) -> list[dict]:
    baseline_index = {row_key(row): row for row in baseline_rows}
    candidate_index = {row_key(row): row for row in candidate_rows}
    diffs = []
    for key in sorted(set(baseline_index) | set(candidate_index)):
        baseline = baseline_index.get(key)
        candidate = candidate_index.get(key)
        baseline_channel = baseline["channel"] if baseline else None
        candidate_channel = candidate["channel"] if candidate else None
        baseline_reason = baseline["reason"] if baseline else None
        candidate_reason = candidate["reason"] if candidate else None
        if baseline_channel != candidate_channel or baseline_reason != candidate_reason:
            diffs.append(
                {
                    "event_name": key[0],
                    "severity": key[1],
                    "gate": key[2],
                    "baseline_channel": baseline_channel,
                    "candidate_channel": candidate_channel,
                    "baseline_reason": baseline_reason,
                    "candidate_reason": candidate_reason,
                }
            )
    return diffs


def format_markdown(diffs: list[dict]) -> str:
    lines = [
        "# Notification Route Diff",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat()}",
        f"- Changed rows: {len(diffs)}",
        "",
        "| Event | Severity | Gate | Baseline | Candidate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in diffs:
        lines.append(
            f"| {row['event_name']} | {row['severity']} | {row['gate']} | "
            f"{row['baseline_channel']} | {row['candidate_channel']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    baseline_rows = load_rows(args.baseline)
    candidate_rows = load_rows(args.candidate)
    diffs = compare_rows(baseline_rows, candidate_rows)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "baseline": args.baseline,
        "candidate": args.candidate,
        "changed_rows": len(diffs),
        "diffs": diffs,
    }

    print(f"changed_rows={len(diffs)}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved route diff to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_markdown(diffs), encoding="utf-8")
        print(f"saved markdown route diff to {md_output_path}")


if __name__ == "__main__":
    main()
