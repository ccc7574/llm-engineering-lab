from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--channel", choices=["stdout", "slack_webhook", "feishu_webhook"], default="stdout")
    parser.add_argument("--webhook-url", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_payload(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve_webhook_url(channel: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env_var = {
        "slack_webhook": "SLACK_WEBHOOK_URL",
        "feishu_webhook": "FEISHU_WEBHOOK_URL",
    }.get(channel)
    if not env_var:
        return None
    return os.environ.get(env_var)


def send_webhook(url: str, payload: dict) -> tuple[bool, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            status_code = response.getcode()
            response_text = response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        return False, str(exc)
    return 200 <= status_code < 300, response_text


def main() -> None:
    args = parse_args()
    payload = load_payload(args.payload)

    if args.channel == "stdout":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    webhook_url = resolve_webhook_url(args.channel, args.webhook_url)
    if not webhook_url:
        print("missing webhook url", file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        print(f"dry-run channel={args.channel}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    ok, response_text = send_webhook(webhook_url, payload)
    if not ok:
        print(response_text, file=sys.stderr)
        sys.exit(1)
    print(response_text)


if __name__ == "__main__":
    main()
