from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", default="runs/notification_digest.json")
    parser.add_argument("--slack-output", default=None)
    parser.add_argument("--feishu-output", default=None)
    return parser.parse_args()


def load_digest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def severity_emoji(severity: str) -> str:
    return {
        "critical": ":red_circle:",
        "warning": ":large_orange_circle:",
        "info": ":large_green_circle:",
    }.get(severity, ":white_circle:")


def build_summary_lines(digest: dict) -> list[str]:
    lines = [
        f"Gate: `{digest.get('overall_gate')}`",
        f"Suite: `{digest.get('suite_status')}`",
        f"Run Mode: `{digest.get('run_mode')}`",
        f"Steps: `{digest.get('steps_passed')}/{digest.get('steps_total')}`",
    ]
    active_scopes = digest.get("active_scopes") or []
    if active_scopes:
        lines.append(f"Scopes: `{', '.join(active_scopes)}`")
    return lines


def build_slack_payload(digest: dict) -> dict:
    text_lines = [
        f"{severity_emoji(digest['severity'])} {digest['headline']}",
        *build_summary_lines(digest),
    ]
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": digest["headline"]},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "\n".join(f"- {line}" for line in build_summary_lines(digest))},
        },
    ]
    failed_steps = digest.get("failed_steps", [])
    if failed_steps:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(
                        f"- `{row['name']}` | `{row['failure_category']}` | {row['failure_summary']}"
                        for row in failed_steps[:8]
                    ),
                },
            }
        )
    return {
        "text": "\n".join(text_lines),
        "blocks": blocks,
    }


def build_feishu_payload(digest: dict) -> dict:
    content = [
        [{"tag": "text", "text": f"{digest['headline']}\n"}],
        [{"tag": "text", "text": "\n".join(build_summary_lines(digest))}],
    ]
    failed_steps = digest.get("failed_steps", [])
    if failed_steps:
        content.append([{"tag": "text", "text": "Failed Steps:"}])
        for row in failed_steps[:8]:
            content.append(
                [
                    {
                        "tag": "text",
                        "text": f"{row['name']} | {row['failure_category']} | {row['failure_summary']}",
                    }
                ]
            )
    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": digest["headline"],
                    "content": content,
                }
            }
        },
    }


def main() -> None:
    args = parse_args()
    digest = load_digest(args.digest)
    slack_payload = build_slack_payload(digest)
    feishu_payload = build_feishu_payload(digest)

    if args.slack_output:
        path = Path(args.slack_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(slack_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved slack payload to {path}")
    if args.feishu_output:
        path = Path(args.feishu_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(feishu_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved feishu payload to {path}")


if __name__ == "__main__":
    main()
