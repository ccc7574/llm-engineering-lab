from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--channel", choices=["stdout", "slack_webhook", "feishu_webhook"], default="stdout")
    parser.add_argument("--webhook-url", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=float, default=1.0)
    parser.add_argument("--idempotency-key", default=None)
    parser.add_argument("--state-path", default="runs/notification_dispatch_state.json")
    parser.add_argument("--output", default=None)
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


def build_idempotency_key(channel: str, payload: dict, explicit: str | None) -> str:
    if explicit:
        return explicit
    normalized_payload = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(f"{channel}\n{normalized_payload}".encode("utf-8")).hexdigest()
    return f"{channel}:{digest}"


def load_state(path: str | Path) -> dict:
    state_path = Path(path)
    if not state_path.exists():
        return {"records": {}}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(path: str | Path, payload: dict) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def already_dispatched(state: dict, idempotency_key: str) -> dict | None:
    record = state.get("records", {}).get(idempotency_key)
    if record and record.get("final_status") == "dispatched":
        return record
    return None


def send_webhook(url: str, payload: dict, idempotency_key: str) -> tuple[bool, int | None, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "X-Idempotency-Key": idempotency_key},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            status_code = response.getcode()
            response_text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        response_text = exc.read().decode("utf-8", errors="replace")
        return False, status_code, response_text
    except urllib.error.URLError as exc:
        return False, None, str(exc)
    return 200 <= status_code < 300, status_code, response_text


def execute_dispatch(
    *,
    channel: str,
    payload: dict,
    webhook_url: str | None,
    dry_run: bool,
    max_attempts: int,
    retry_delay_seconds: float,
    idempotency_key: str,
    state_path: str | Path,
) -> dict:
    state = load_state(state_path)
    duplicate_record = already_dispatched(state, idempotency_key)
    if duplicate_record:
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "channel": channel,
            "idempotency_key": idempotency_key,
            "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "final_status": "skipped_duplicate",
            "dispatched": False,
            "dry_run": dry_run,
            "skipped_duplicate": True,
            "attempt_count": 0,
            "http_status": duplicate_record.get("http_status"),
            "response_text": "duplicate dispatch suppressed by idempotency state",
        }

    if channel == "stdout":
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "channel": channel,
            "idempotency_key": idempotency_key,
            "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "final_status": "printed",
            "dispatched": False,
            "dry_run": dry_run,
            "skipped_duplicate": False,
            "attempt_count": 0,
            "http_status": None,
            "response_text": json.dumps(payload, indent=2, ensure_ascii=False),
        }

    if not webhook_url:
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "channel": channel,
            "idempotency_key": idempotency_key,
            "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "final_status": "missing_webhook",
            "dispatched": False,
            "dry_run": dry_run,
            "skipped_duplicate": False,
            "attempt_count": 0,
            "http_status": None,
            "response_text": "missing webhook url",
        }

    if dry_run:
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "channel": channel,
            "idempotency_key": idempotency_key,
            "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "final_status": "dry_run",
            "dispatched": False,
            "dry_run": True,
            "skipped_duplicate": False,
            "attempt_count": 0,
            "http_status": None,
            "response_text": json.dumps(payload, indent=2, ensure_ascii=False),
        }

    attempts: list[dict] = []
    for attempt in range(1, max(1, max_attempts) + 1):
        ok, http_status, response_text = send_webhook(webhook_url, payload, idempotency_key)
        attempts.append(
            {
                "attempt": attempt,
                "ok": ok,
                "http_status": http_status,
                "response_text": response_text,
            }
        )
        if ok:
            result = {
                "generated_at": datetime.now().astimezone().isoformat(),
                "channel": channel,
                "idempotency_key": idempotency_key,
                "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
                "final_status": "dispatched",
                "dispatched": True,
                "dry_run": False,
                "skipped_duplicate": False,
                "attempt_count": attempt,
                "http_status": http_status,
                "response_text": response_text,
                "attempts": attempts,
            }
            state.setdefault("records", {})[idempotency_key] = result
            save_state(state_path, state)
            return result
        if attempt < max_attempts and retry_delay_seconds > 0:
            time.sleep(retry_delay_seconds)

    result = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "channel": channel,
        "idempotency_key": idempotency_key,
        "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
        "final_status": "failed",
        "dispatched": False,
        "dry_run": False,
        "skipped_duplicate": False,
        "attempt_count": len(attempts),
        "http_status": attempts[-1]["http_status"] if attempts else None,
        "response_text": attempts[-1]["response_text"] if attempts else "dispatch failed",
        "attempts": attempts,
    }
    return result


def main() -> None:
    args = parse_args()
    payload = load_payload(args.payload)
    idempotency_key = build_idempotency_key(args.channel, payload, args.idempotency_key)

    webhook_url = resolve_webhook_url(args.channel, args.webhook_url)
    result = execute_dispatch(
        channel=args.channel,
        payload=payload,
        webhook_url=webhook_url,
        dry_run=args.dry_run,
        max_attempts=args.max_attempts,
        retry_delay_seconds=args.retry_delay_seconds,
        idempotency_key=idempotency_key,
        state_path=args.state_path,
    )

    print(f"final_status={result['final_status']}")
    print(f"idempotency_key={result['idempotency_key']}")
    print(f"attempt_count={result['attempt_count']}")
    if result.get("http_status") is not None:
        print(f"http_status={result['http_status']}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved dispatch result to {output_path}")

    if args.channel == "stdout":
        print(result["response_text"])
        return
    if result["final_status"] == "missing_webhook":
        print(result["response_text"], file=sys.stderr)
        sys.exit(2)
    if result["final_status"] == "failed":
        print(result["response_text"], file=sys.stderr)
        sys.exit(1)
    if result["final_status"] == "dry_run":
        print(f"dry-run channel={args.channel}")
        print(result["response_text"])
        return
    if result["final_status"] == "skipped_duplicate":
        print(result["response_text"])
        return
    print(result["response_text"])


if __name__ == "__main__":
    main()
