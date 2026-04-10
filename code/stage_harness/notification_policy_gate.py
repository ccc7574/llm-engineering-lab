from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-diff", default="runs/notification_route_diff.json")
    parser.add_argument("--policy", default="manifests/notification_policy_gate.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--fail-on-non-ship", action="store_true")
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def diff_key(row: dict) -> tuple[str, str, str, str]:
    return row["event_name"], row["severity"], row["gate"], row.get("failure_category", "none")


def evaluate_gate(route_diff: dict, policy: dict, route_diff_path: str, policy_path: str) -> dict:
    allowed = {
        (row["event_name"], row["severity"], row["gate"], row.get("failure_category", "none"))
        for row in policy.get("allowed_changes", [])
    }
    max_changed_rows = int(policy.get("max_changed_rows", 0))
    diffs = list(route_diff.get("diffs", []))
    unexpected = [row for row in diffs if diff_key(row) not in allowed]

    decision = "ship"
    reason = "all route policy changes are within the configured gate"
    if len(diffs) > max_changed_rows:
        decision = "hold"
        reason = f"changed rows {len(diffs)} exceed max_changed_rows {max_changed_rows}"
    elif unexpected:
        decision = "hold"
        reason = "route diff contains unexpected event/severity/gate/failure_category changes"

    return {
        "route_diff": route_diff_path,
        "policy": policy_path,
        "decision": decision,
        "reason": reason,
        "changed_rows": len(diffs),
        "unexpected_rows": len(unexpected),
        "max_changed_rows": max_changed_rows,
        "unexpected_diffs": unexpected,
    }


def main() -> None:
    args = parse_args()
    route_diff = load_json(args.route_diff)
    policy = load_json(args.policy)
    payload = evaluate_gate(route_diff, policy, args.route_diff, args.policy)

    print(f"decision={payload['decision']}")
    print(f"reason={payload['reason']}")
    print(f"changed_rows={payload['changed_rows']}")
    print(f"unexpected_rows={payload['unexpected_rows']}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved policy gate report to {output_path}")

    if args.fail_on_non_ship and payload["decision"] != "ship":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
