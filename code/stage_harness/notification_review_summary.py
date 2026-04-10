from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", default="runs/notification_digest.json")
    parser.add_argument("--route", default="runs/notification_route.json")
    parser.add_argument("--policy-gate", default="runs/notification_policy_gate.json")
    parser.add_argument("--dispatch-policy", default="runs/notification_dispatch_policy.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def top_failure_category(digest: dict) -> str | None:
    counts = Counter(digest.get("failure_counts", {}))
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def build_reviewer_notes(digest: dict, route: dict, policy_gate: dict, dispatch_policy: dict) -> list[str]:
    notes = []
    if digest.get("ship_ready"):
        notes.append("Regression suite is ship-ready from the current suite and release gate perspective.")
    else:
        notes.append("Regression suite is not ship-ready; review failed steps and gate decision before merge or release.")

    if policy_gate.get("decision") == "ship":
        notes.append("Notification routing policy diff is within the configured review boundary.")
    else:
        notes.append(f"Notification routing policy needs review: {policy_gate.get('reason')}")

    if dispatch_policy.get("allow_dispatch"):
        notes.append(f"Live notification dispatch is allowed on `{route.get('channel')}` for this run.")
    elif route.get("channel") != "none":
        notes.append(f"Notification was routed to `{route.get('channel')}` but suppressed by dispatch policy.")
    else:
        notes.append("No live notification channel is selected for this run.")

    failure_category = top_failure_category(digest)
    if failure_category:
        notes.append(f"Top failure category is `{failure_category}`, which should drive the first triage pass.")

    return notes


def build_summary(digest: dict, route: dict, policy_gate: dict, dispatch_policy: dict) -> dict:
    notes = build_reviewer_notes(digest, route, policy_gate, dispatch_policy)
    failed_step_names = [row.get("name") for row in digest.get("failed_steps", [])]
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "headline": digest.get("headline"),
        "severity": digest.get("severity"),
        "suite_status": digest.get("suite_status"),
        "overall_gate": digest.get("overall_gate"),
        "ship_ready": bool(digest.get("ship_ready")),
        "event_name": route.get("event_name"),
        "route_channel": route.get("channel"),
        "route_reason": route.get("reason"),
        "override_applied": bool(route.get("override_applied")),
        "dispatch_allowed": bool(dispatch_policy.get("allow_dispatch")),
        "dispatch_reason": dispatch_policy.get("reason"),
        "dispatch_rule": dispatch_policy.get("matched_rule"),
        "policy_gate_decision": policy_gate.get("decision"),
        "policy_gate_reason": policy_gate.get("reason"),
        "route_diff_changed_rows": policy_gate.get("changed_rows"),
        "active_scopes": digest.get("active_scopes", []),
        "failed_steps": failed_step_names,
        "failure_counts": digest.get("failure_counts", {}),
        "reviewer_notes": notes,
    }


def format_markdown(summary: dict) -> str:
    lines = [
        "# Notification Review Summary",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Headline: {summary['headline']}",
        f"- Event: {summary['event_name']}",
        f"- Severity: {summary['severity']}",
        f"- Suite status: {summary['suite_status']}",
        f"- Release gate: {summary['overall_gate']}",
        f"- Route channel: {summary['route_channel']}",
        f"- Route override: {str(summary['override_applied']).lower()}",
        f"- Dispatch allowed: {str(summary['dispatch_allowed']).lower()}",
        f"- Policy gate: {summary['policy_gate_decision']}",
        f"- Route diff changed rows: {summary['route_diff_changed_rows']}",
    ]
    if summary.get("active_scopes"):
        lines.append(f"- Active scopes: {', '.join(summary['active_scopes'])}")

    lines.extend(["", "## Reviewer Notes", ""])
    for note in summary.get("reviewer_notes", []):
        lines.append(f"- {note}")

    if summary.get("failed_steps"):
        lines.extend(["", "## Failed Steps", ""])
        for name in summary["failed_steps"][:8]:
            lines.append(f"- `{name}`")

    if summary.get("failure_counts"):
        lines.extend(["", "## Failure Counts", ""])
        for category, count in sorted(summary["failure_counts"].items()):
            lines.append(f"- `{category}`: {count}")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    digest = load_json(args.digest)
    route = load_json(args.route)
    policy_gate = load_json(args.policy_gate)
    dispatch_policy = load_json(args.dispatch_policy)
    summary = build_summary(digest, route, policy_gate, dispatch_policy)

    print(f"route_channel={summary['route_channel']}")
    print(f"dispatch_allowed={str(summary['dispatch_allowed']).lower()}")
    print(f"policy_gate={summary['policy_gate_decision']}")
    print(f"reviewer_notes={len(summary['reviewer_notes'])}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved review summary to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_markdown(summary), encoding="utf-8")
        print(f"saved markdown review summary to {md_output_path}")


if __name__ == "__main__":
    main()
