from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stage_harness.notification_route import load_json, select_route


DEFAULT_EVENTS = ["pull_request", "push", "workflow_dispatch", "schedule"]
DEFAULT_SEVERITIES = ["info", "warning", "critical"]
DEFAULT_GATES = ["ship", "hold", "block"]
DEFAULT_FAILURE_CATEGORIES = ["none", "process_error", "permission_error", "report_parse_error"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", default="manifests/notification_routes.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def failure_profiles_for_severity(severity: str) -> list[str]:
    return ["none"] if severity == "info" else list(DEFAULT_FAILURE_CATEGORIES)


def build_digest(severity: str, gate: str, failure_category: str) -> dict:
    failure_counts = {} if failure_category == "none" else {failure_category: 1}
    return {
        "severity": severity,
        "overall_gate": gate,
        "ship_ready": severity == "info" and gate == "ship",
        "headline": f"sample {severity}",
        "failure_counts": failure_counts,
        "top_failure_category": None if failure_category == "none" else failure_category,
    }


def build_matrix(routes: dict) -> list[dict]:
    rows = []
    for event_name in DEFAULT_EVENTS:
        for severity in DEFAULT_SEVERITIES:
            for gate in DEFAULT_GATES:
                for failure_category in failure_profiles_for_severity(severity):
                    digest = build_digest(severity, gate, failure_category)
                    route = select_route(
                        digest=digest,
                        routes=routes,
                        event_name=event_name,
                        default_channel="none",
                        override_channel=None,
                    )
                    rows.append(
                        {
                            "event_name": event_name,
                            "severity": severity,
                            "gate": gate,
                            "failure_category": failure_category,
                            "ship_ready": digest["ship_ready"],
                            "channel": route["channel"],
                            "reason": route["reason"],
                        }
                    )
    return rows


def format_markdown(rows: list[dict]) -> str:
    lines = [
        "# Notification Route Matrix",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat()}",
        "",
        "| Event | Severity | Gate | Failure Category | Ship Ready | Channel | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['event_name']} | {row['severity']} | {row['gate']} | "
            f"{row['failure_category']} | {str(row['ship_ready']).lower()} | {row['channel']} | {row['reason']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    routes = load_json(args.routes)
    rows = build_matrix(routes)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "routes_path": args.routes,
        "rows": rows,
    }

    print(f"matrix_rows={len(rows)}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved matrix to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_markdown(rows), encoding="utf-8")
        print(f"saved markdown matrix to {md_output_path}")


if __name__ == "__main__":
    main()
