from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import time
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


CHANNEL_CONFIG = {
    "slack_webhook": {
        "provider": "slack",
        "base_backoff_seconds": 1.0,
        "allowed_hosts": {"hooks.slack.com", "hooks.slack-gov.com"},
    },
    "feishu_webhook": {
        "provider": "feishu",
        "base_backoff_seconds": 1.5,
        "allowed_hosts": {"open.feishu.cn", "open.larksuite.com"},
    },
    "stdout": {"provider": "stdout", "base_backoff_seconds": 0.0, "allowed_hosts": set()},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--channel", choices=["stdout", "slack_webhook", "feishu_webhook"], default="stdout")
    parser.add_argument("--webhook-url", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=float, default=1.0)
    parser.add_argument("--idempotency-key", default=None)
    parser.add_argument("--signing-secret", default=None)
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


def resolve_signing_secret(channel: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env_var = {
        "feishu_webhook": "FEISHU_WEBHOOK_SECRET",
    }.get(channel)
    if not env_var:
        return None
    return os.environ.get(env_var)


def detect_webhook_source(channel: str, explicit: str | None) -> str:
    if explicit:
        return "argument"
    env_var = {
        "slack_webhook": "SLACK_WEBHOOK_URL",
        "feishu_webhook": "FEISHU_WEBHOOK_URL",
    }.get(channel)
    if env_var and os.environ.get(env_var):
        return env_var
    return "missing"


def detect_signing_secret_source(channel: str, explicit: str | None) -> str:
    if explicit:
        return "argument"
    env_var = {
        "feishu_webhook": "FEISHU_WEBHOOK_SECRET",
    }.get(channel)
    if env_var and os.environ.get(env_var):
        return env_var
    return "none"


def validate_webhook_url(channel: str, webhook_url: str | None) -> dict:
    if not webhook_url:
        return {
            "ok": False,
            "category": "missing_webhook",
            "message": "missing webhook url",
            "host": None,
            "scheme": None,
        }
    parsed = urlparse(webhook_url)
    host = (parsed.hostname or "").lower()
    allowed_hosts = CHANNEL_CONFIG.get(channel, {}).get("allowed_hosts", set())
    if parsed.scheme != "https":
        return {
            "ok": False,
            "category": "invalid_webhook_scheme",
            "message": "webhook url must use https",
            "host": host,
            "scheme": parsed.scheme or None,
        }
    if allowed_hosts and host not in allowed_hosts:
        return {
            "ok": False,
            "category": "untrusted_webhook_host",
            "message": f"webhook host {host!r} is not allowed for channel {channel}",
            "host": host,
            "scheme": parsed.scheme,
        }
    return {
        "ok": True,
        "category": "validated",
        "message": "webhook url passed provider host validation",
        "host": host,
        "scheme": parsed.scheme,
    }


def build_feishu_signature(secret: str, timestamp: int) -> str:
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    signature = hmac.new(string_to_sign, digestmod=hashlib.sha256).digest()
    return base64.b64encode(signature).decode("utf-8")


def prepare_dispatch_request(
    channel: str,
    payload: dict,
    signing_secret: str | None,
) -> tuple[dict, dict]:
    request_payload = dict(payload)
    security_context = {
        "signed_request": False,
        "signature_mode": "none",
        "signing_secret_present": bool(signing_secret),
    }
    if channel == "feishu_webhook" and signing_secret:
        timestamp = int(time.time())
        request_payload["timestamp"] = str(timestamp)
        request_payload["sign"] = build_feishu_signature(signing_secret, timestamp)
        security_context["signed_request"] = True
        security_context["signature_mode"] = "feishu_custom_bot_secret"
    return request_payload, security_context


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


def parse_retry_after(headers: dict[str, str]) -> float | None:
    retry_after = headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        return float(retry_after)
    except ValueError:
        return None


def parse_json_response(text: str) -> dict | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def classify_dispatch_response(
    channel: str,
    http_status: int | None,
    response_text: str,
    headers: dict[str, str],
) -> dict:
    provider = CHANNEL_CONFIG.get(channel, {}).get("provider", channel)
    retry_after_seconds = parse_retry_after(headers)
    parsed_json = parse_json_response(response_text)
    lower_text = response_text.lower()

    ack_status = "unknown"
    failure_category = "unknown"
    retryable = False

    if channel == "slack_webhook":
        if http_status == 200 and response_text.strip().lower() == "ok":
            ack_status = "ok"
            failure_category = "success"
        elif http_status == 429:
            ack_status = "rate_limited"
            failure_category = "rate_limit"
            retryable = True
        elif http_status is not None and http_status >= 500:
            ack_status = "provider_error"
            failure_category = "provider_error"
            retryable = True
        elif http_status in {400, 403, 404}:
            ack_status = "rejected"
            failure_category = "permanent_rejection"
        elif http_status is None:
            ack_status = "network_error"
            failure_category = "network_error"
            retryable = True
    elif channel == "feishu_webhook":
        code = None if not parsed_json else parsed_json.get("code", parsed_json.get("StatusCode", parsed_json.get("status", parsed_json.get("statusCode"))))
        message = None if not parsed_json else parsed_json.get("msg", parsed_json.get("StatusMessage", parsed_json.get("message")))
        if http_status == 200 and code in {0, "0", None} and ("success" in lower_text or parsed_json is not None):
            ack_status = "ok"
            failure_category = "success"
        elif http_status == 429 or "rate limit" in lower_text or "too many" in lower_text:
            ack_status = "rate_limited"
            failure_category = "rate_limit"
            retryable = True
        elif http_status is not None and http_status >= 500:
            ack_status = "provider_error"
            failure_category = "provider_error"
            retryable = True
        elif http_status is None:
            ack_status = "network_error"
            failure_category = "network_error"
            retryable = True
        elif parsed_json is not None:
            ack_status = "rejected"
            failure_category = "permanent_rejection"
            if message and any(token in message.lower() for token in ["tempor", "retry", "later", "timeout"]):
                retryable = True
                failure_category = "transient_rejection"
    else:
        if http_status is None:
            ack_status = "network_error"
            failure_category = "network_error"
            retryable = True
        elif 200 <= http_status < 300:
            ack_status = "ok"
            failure_category = "success"
        elif http_status == 429:
            ack_status = "rate_limited"
            failure_category = "rate_limit"
            retryable = True
        elif http_status >= 500:
            ack_status = "provider_error"
            failure_category = "provider_error"
            retryable = True
        else:
            ack_status = "rejected"
            failure_category = "permanent_rejection"

    success = ack_status == "ok"
    return {
        "provider": provider,
        "ack_status": ack_status,
        "failure_category": failure_category,
        "retryable": retryable,
        "retry_after_seconds": retry_after_seconds,
        "success": success,
        "provider_payload": parsed_json,
    }


def compute_backoff_seconds(channel: str, attempt: int, retry_after_seconds: float | None) -> float:
    if retry_after_seconds is not None:
        return retry_after_seconds
    base = CHANNEL_CONFIG.get(channel, {}).get("base_backoff_seconds", 1.0)
    exponent = max(0, attempt - 1)
    return base * (2**exponent)


def send_webhook(url: str, payload: dict, idempotency_key: str) -> tuple[int | None, str, dict[str, str]]:
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
            raw_headers = getattr(response, "headers", None)
            headers = dict(raw_headers.items()) if raw_headers else {}
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        response_text = exc.read().decode("utf-8", errors="replace")
        headers = dict(exc.headers.items()) if exc.headers else {}
        return status_code, response_text, headers
    except urllib.error.URLError as exc:
        return None, str(exc), {}
    return status_code, response_text, headers


def execute_dispatch(
    *,
    channel: str,
    payload: dict,
    webhook_url: str | None,
    dry_run: bool,
    max_attempts: int,
    retry_delay_seconds: float,
    idempotency_key: str,
    signing_secret: str | None = None,
    webhook_source: str | None = None,
    signing_secret_source: str | None = None,
    state_path: str | Path,
) -> dict:
    webhook_source = webhook_source or ("provided" if webhook_url else "missing")
    signing_secret_source = signing_secret_source or ("provided" if signing_secret else "none")
    url_validation = validate_webhook_url(channel, webhook_url)
    request_payload, security_context = prepare_dispatch_request(channel, payload, signing_secret)
    state = load_state(state_path)
    duplicate_record = already_dispatched(state, idempotency_key)
    if duplicate_record:
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "channel": channel,
            "provider": CHANNEL_CONFIG.get(channel, {}).get("provider", channel),
            "idempotency_key": idempotency_key,
            "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "final_status": "skipped_duplicate",
            "dispatched": False,
            "dry_run": dry_run,
            "skipped_duplicate": True,
            "attempt_count": 0,
            "http_status": duplicate_record.get("http_status"),
            "ack_status": duplicate_record.get("ack_status"),
            "failure_category": "duplicate_suppressed",
            "response_text": "duplicate dispatch suppressed by idempotency state",
            "security": {
                "webhook_source": webhook_source,
                "signing_secret_source": signing_secret_source,
                "url_validation": url_validation,
                **security_context,
            },
        }

    if channel == "stdout":
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "channel": channel,
            "provider": CHANNEL_CONFIG.get(channel, {}).get("provider", channel),
            "idempotency_key": idempotency_key,
            "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "final_status": "printed",
            "dispatched": False,
            "dry_run": dry_run,
            "skipped_duplicate": False,
            "attempt_count": 0,
            "http_status": None,
            "ack_status": "local_print",
            "failure_category": "not_applicable",
            "response_text": json.dumps(request_payload, indent=2, ensure_ascii=False),
            "security": {
                "webhook_source": webhook_source,
                "signing_secret_source": signing_secret_source,
                "url_validation": url_validation,
                **security_context,
            },
        }

    if not url_validation["ok"]:
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "channel": channel,
            "provider": CHANNEL_CONFIG.get(channel, {}).get("provider", channel),
            "idempotency_key": idempotency_key,
            "payload_size_bytes": len(json.dumps(request_payload, ensure_ascii=False).encode("utf-8")),
            "final_status": url_validation["category"],
            "dispatched": False,
            "dry_run": dry_run,
            "skipped_duplicate": False,
            "attempt_count": 0,
            "http_status": None,
            "ack_status": url_validation["category"],
            "failure_category": "configuration_error",
            "response_text": url_validation["message"],
            "security": {
                "webhook_source": webhook_source,
                "signing_secret_source": signing_secret_source,
                "url_validation": url_validation,
                **security_context,
            },
        }

    if dry_run:
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "channel": channel,
            "provider": CHANNEL_CONFIG.get(channel, {}).get("provider", channel),
            "idempotency_key": idempotency_key,
            "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "final_status": "dry_run",
            "dispatched": False,
            "dry_run": True,
            "skipped_duplicate": False,
            "attempt_count": 0,
            "http_status": None,
            "ack_status": "dry_run",
            "failure_category": "not_applicable",
            "response_text": json.dumps(request_payload, indent=2, ensure_ascii=False),
            "security": {
                "webhook_source": webhook_source,
                "signing_secret_source": signing_secret_source,
                "url_validation": url_validation,
                **security_context,
            },
        }

    attempts: list[dict] = []
    for attempt in range(1, max(1, max_attempts) + 1):
        http_status, response_text, headers = send_webhook(webhook_url, request_payload, idempotency_key)
        classification = classify_dispatch_response(channel, http_status, response_text, headers)
        delay_seconds = compute_backoff_seconds(channel, attempt, classification["retry_after_seconds"])
        attempts.append(
            {
                "attempt": attempt,
                "ok": classification["success"],
                "http_status": http_status,
                "ack_status": classification["ack_status"],
                "failure_category": classification["failure_category"],
                "retryable": classification["retryable"],
                "retry_after_seconds": classification["retry_after_seconds"],
                "next_delay_seconds": delay_seconds if classification["retryable"] and attempt < max_attempts else 0.0,
                "response_text": response_text,
            }
        )
        if classification["success"]:
            result = {
                "generated_at": datetime.now().astimezone().isoformat(),
                "channel": channel,
                "provider": classification["provider"],
                "idempotency_key": idempotency_key,
                "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
                "final_status": "dispatched",
                "dispatched": True,
                "dry_run": False,
                "skipped_duplicate": False,
                "attempt_count": attempt,
                "http_status": http_status,
                "ack_status": classification["ack_status"],
                "failure_category": classification["failure_category"],
                "response_text": response_text,
                "attempts": attempts,
                "security": {
                    "webhook_source": webhook_source,
                    "signing_secret_source": signing_secret_source,
                    "url_validation": url_validation,
                    **security_context,
                },
            }
            state.setdefault("records", {})[idempotency_key] = result
            save_state(state_path, state)
            return result
        if not classification["retryable"]:
            break
        if attempt < max_attempts:
            sleep_seconds = max(delay_seconds, retry_delay_seconds)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    result = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "channel": channel,
        "provider": CHANNEL_CONFIG.get(channel, {}).get("provider", channel),
        "idempotency_key": idempotency_key,
        "payload_size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
        "final_status": "failed",
        "dispatched": False,
        "dry_run": False,
        "skipped_duplicate": False,
        "attempt_count": len(attempts),
        "http_status": attempts[-1]["http_status"] if attempts else None,
        "ack_status": attempts[-1]["ack_status"] if attempts else "unknown",
        "failure_category": attempts[-1]["failure_category"] if attempts else "unknown",
        "response_text": attempts[-1]["response_text"] if attempts else "dispatch failed",
        "attempts": attempts,
        "security": {
            "webhook_source": webhook_source,
            "signing_secret_source": signing_secret_source,
            "url_validation": url_validation,
            **security_context,
        },
    }
    return result


def main() -> None:
    args = parse_args()
    payload = load_payload(args.payload)
    idempotency_key = build_idempotency_key(args.channel, payload, args.idempotency_key)

    webhook_url = resolve_webhook_url(args.channel, args.webhook_url)
    signing_secret = resolve_signing_secret(args.channel, args.signing_secret)
    result = execute_dispatch(
        channel=args.channel,
        payload=payload,
        webhook_url=webhook_url,
        dry_run=args.dry_run,
        max_attempts=args.max_attempts,
        retry_delay_seconds=args.retry_delay_seconds,
        idempotency_key=idempotency_key,
        signing_secret=signing_secret,
        webhook_source=detect_webhook_source(args.channel, args.webhook_url),
        signing_secret_source=detect_signing_secret_source(args.channel, args.signing_secret),
        state_path=args.state_path,
    )

    print(f"final_status={result['final_status']}")
    print(f"idempotency_key={result['idempotency_key']}")
    print(f"attempt_count={result['attempt_count']}")
    print(f"ack_status={result['ack_status']}")
    print(f"failure_category={result['failure_category']}")
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
    if result["final_status"] in {"missing_webhook", "invalid_webhook_scheme", "untrusted_webhook_host"}:
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
