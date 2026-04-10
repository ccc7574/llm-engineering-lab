from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-diff", default="runs/notification_route_diff.json")
    parser.add_argument("--policy", default="manifests/notification_policy_gate.json")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def diff_key(row: dict) -> tuple[str, str, str]:
    return row["event_name"], row["severity"], row["gate"]


def main() -> None:
    args = parse_args()
    route_diff = load_json(args.route_diff)
    policy = load_json(args.policy)

    allowed = {
        (row["event_name"], row["severity"], row["gate"])
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
        reason = "route diff contains unexpected event/severity/gate changes"

    print(f"decision={decision}")
    print(f"reason={reason}")
    print(f"changed_rows={len(diffs)}")
    print(f"unexpected_rows={len(unexpected)}")

    payload = {
        "route_diff": args.route_diff,
        "policy": args.policy,
        "decision": decision,
        "reason": reason,
        "changed_rows": len(diffs),
        "unexpected_rows": len(unexpected),
        "max_changed_rows": max_changed_rows,
        "unexpected_diffs": unexpected,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved policy gate report to {output_path}")

    if decision != "ship":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
