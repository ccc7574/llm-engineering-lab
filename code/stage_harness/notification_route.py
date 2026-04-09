from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", default="runs/notification_digest.json")
    parser.add_argument("--routes", default="manifests/notification_routes.json")
    parser.add_argument("--event-name", default="workflow_dispatch")
    parser.add_argument("--default-channel", default="none")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def matches(rule: dict, digest: dict, event_name: str) -> bool:
    event_names = rule.get("event_names", [])
    severities = rule.get("severities", [])
    gates = rule.get("gates", [])
    ship_ready = rule.get("ship_ready")

    if event_names and event_name not in event_names:
        return False
    if severities and digest.get("severity") not in severities:
        return False
    if gates and digest.get("overall_gate") not in gates:
        return False
    if ship_ready is not None and bool(digest.get("ship_ready")) != bool(ship_ready):
        return False
    return True


def select_route(digest: dict, routes: dict, event_name: str, default_channel: str) -> dict:
    for rule in routes.get("rules", []):
        if matches(rule, digest, event_name):
            channel = rule["channel"]
            return {
                "event_name": event_name,
                "channel": channel,
                "reason": rule.get("reason", "matched notification routing rule"),
                "payload_path": routes.get("channel_payloads", {}).get(channel),
            }
    return {
        "event_name": event_name,
        "channel": default_channel,
        "reason": "no routing rule matched",
        "payload_path": routes.get("channel_payloads", {}).get(default_channel),
    }


def main() -> None:
    args = parse_args()
    digest = load_json(args.digest)
    routes = load_json(args.routes)
    route = select_route(digest, routes, args.event_name, args.default_channel)
    route["severity"] = digest.get("severity")
    route["headline"] = digest.get("headline")
    route["ship_ready"] = digest.get("ship_ready")

    print(f"channel={route['channel']}")
    print(f"reason={route['reason']}")
    print(f"payload_path={route.get('payload_path')}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(route, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved route to {output_path}")


if __name__ == "__main__":
    main()
