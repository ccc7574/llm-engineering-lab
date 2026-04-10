from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", default="runs/notification_digest.json")
    parser.add_argument("--route", default="runs/notification_route.json")
    parser.add_argument("--policy", default="manifests/notification_dispatch_policy.json")
    parser.add_argument("--event-name", default="workflow_dispatch")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def matches(rule: dict, digest: dict, route: dict, event_name: str) -> bool:
    event_names = rule.get("event_names", [])
    severities = rule.get("severities", [])
    gates = rule.get("gates", [])
    channels = rule.get("channels", [])
    override_applied = rule.get("override_applied")
    ship_ready = rule.get("ship_ready")

    if event_names and event_name not in event_names:
        return False
    if severities and digest.get("severity") not in severities:
        return False
    if gates and digest.get("overall_gate") not in gates:
        return False
    if channels and route.get("channel") not in channels:
        return False
    if override_applied is not None and bool(route.get("override_applied")) != bool(override_applied):
        return False
    if ship_ready is not None and bool(digest.get("ship_ready")) != bool(ship_ready):
        return False
    return True


def evaluate_policy(digest: dict, route: dict, policy: dict, event_name: str) -> dict:
    channel = route.get("channel", "none")
    payload_path = route.get("payload_path")
    base_payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "policy_name": policy.get("policy_name", "notification_dispatch_policy"),
        "event_name": event_name,
        "channel": channel,
        "payload_path": payload_path,
        "override_applied": bool(route.get("override_applied")),
        "severity": digest.get("severity"),
        "overall_gate": digest.get("overall_gate"),
        "ship_ready": bool(digest.get("ship_ready")),
    }

    if channel == "none":
        return {
            **base_payload,
            "allow_dispatch": False,
            "decision": "skip",
            "reason": "route resolved to channel none",
            "matched_rule": None,
        }
    if not payload_path:
        return {
            **base_payload,
            "allow_dispatch": False,
            "decision": "skip",
            "reason": "route does not provide a payload artifact",
            "matched_rule": None,
        }

    for rule in policy.get("rules", []):
        if matches(rule, digest, route, event_name):
            allow_dispatch = bool(rule.get("allow_dispatch"))
            return {
                **base_payload,
                "allow_dispatch": allow_dispatch,
                "decision": "dispatch" if allow_dispatch else "skip",
                "reason": rule.get("reason", "matched dispatch policy rule"),
                "matched_rule": rule.get("name"),
            }

    default_decision = policy.get("default_decision", {})
    allow_dispatch = bool(default_decision.get("allow_dispatch"))
    return {
        **base_payload,
        "allow_dispatch": allow_dispatch,
        "decision": "dispatch" if allow_dispatch else "skip",
        "reason": default_decision.get("reason", "no dispatch policy rule matched"),
        "matched_rule": None,
    }


def main() -> None:
    args = parse_args()
    digest = load_json(args.digest)
    route = load_json(args.route)
    policy = load_json(args.policy)
    payload = evaluate_policy(digest, route, policy, args.event_name)

    print(f"allow_dispatch={str(payload['allow_dispatch']).lower()}")
    print(f"decision={payload['decision']}")
    print(f"reason={payload['reason']}")
    print(f"matched_rule={payload.get('matched_rule')}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved dispatch policy report to {output_path}")


if __name__ == "__main__":
    main()
