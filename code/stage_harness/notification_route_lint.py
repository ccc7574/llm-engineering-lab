from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", default="manifests/notification_routes.json")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def selector_signature(rule: dict) -> tuple:
    return (
        tuple(rule.get("event_names", [])),
        tuple(rule.get("severities", [])),
        tuple(rule.get("gates", [])),
        tuple(rule.get("failure_categories", [])),
        rule.get("ship_ready"),
    )


KNOWN_FAILURE_CATEGORIES = {
    "artifact_missing",
    "dependency_error",
    "logic_error",
    "missing_input",
    "permission_error",
    "process_error",
    "report_parse_error",
    "syntax_error",
    "test_failure",
    "timeout",
    "unknown_failure",
}


def lint_routes(routes: dict) -> list[dict]:
    issues: list[dict] = []
    channel_payloads = routes.get("channel_payloads", {})
    seen_selectors: dict[tuple, int] = {}
    for idx, rule in enumerate(routes.get("rules", [])):
        channel = rule.get("channel")
        if channel not in channel_payloads:
            issues.append(
                {
                    "rule_index": idx,
                    "severity": "error",
                    "type": "unknown_channel",
                    "message": f"rule references unknown channel: {channel}",
                }
            )
        if not rule.get("reason"):
            issues.append(
                {
                    "rule_index": idx,
                    "severity": "warning",
                    "type": "missing_reason",
                    "message": "rule should include a human-readable reason",
                }
            )
        unknown_failure_categories = sorted(
            category
            for category in rule.get("failure_categories", [])
            if category not in KNOWN_FAILURE_CATEGORIES
        )
        if unknown_failure_categories:
            issues.append(
                {
                    "rule_index": idx,
                    "severity": "warning",
                    "type": "unknown_failure_category",
                    "message": f"rule references unknown failure categories: {', '.join(unknown_failure_categories)}",
                }
            )
        signature = selector_signature(rule)
        if signature in seen_selectors:
            issues.append(
                {
                    "rule_index": idx,
                    "severity": "warning",
                    "type": "duplicate_selector",
                    "message": f"rule duplicates selector shape of rule {seen_selectors[signature]}",
                }
            )
        else:
            seen_selectors[signature] = idx
    return issues


def main() -> None:
    args = parse_args()
    routes = load_json(args.routes)
    issues = lint_routes(routes)
    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")

    print(f"errors={error_count}")
    print(f"warnings={warning_count}")
    for issue in issues:
        print(f"{issue['severity']}\t{issue['type']}\t{issue['message']}")

    payload = {
        "routes": args.routes,
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved route lint report to {output_path}")

    if error_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
