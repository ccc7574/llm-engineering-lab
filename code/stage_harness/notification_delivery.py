from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from code.stage_harness.notification_dispatch import (
        build_idempotency_key,
        detect_signing_secret_source,
        detect_webhook_source,
        execute_dispatch,
        load_payload,
        resolve_signing_secret,
        resolve_webhook_url,
    )
    from code.stage_harness.notification_dispatch_policy import evaluate_policy
    from code.stage_harness.notification_route import load_json, select_route
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from stage_harness.notification_dispatch import (  # type: ignore
        build_idempotency_key,
        detect_signing_secret_source,
        detect_webhook_source,
        execute_dispatch,
        load_payload,
        resolve_signing_secret,
        resolve_webhook_url,
    )
    from stage_harness.notification_dispatch_policy import evaluate_policy  # type: ignore
    from stage_harness.notification_route import load_json, select_route  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", default="runs/notification_digest.json")
    parser.add_argument("--routes", default="manifests/notification_routes.json")
    parser.add_argument("--dispatch-policy", default="manifests/notification_dispatch_policy.json")
    parser.add_argument("--event-name", default="workflow_dispatch")
    parser.add_argument("--default-channel", default="none")
    parser.add_argument("--override-channel", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=float, default=1.0)
    parser.add_argument("--idempotency-key", default=None)
    parser.add_argument("--webhook-url", default=None)
    parser.add_argument("--signing-secret", default=None)
    parser.add_argument("--state-path", default="runs/notification_dispatch_state.json")
    parser.add_argument("--route-output", default=None)
    parser.add_argument("--dispatch-policy-output", default=None)
    parser.add_argument("--dispatch-result-output", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def save_json(path: str | Path | None, payload: dict) -> None:
    if not path:
        return
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def build_skipped_dispatch_result(
    *,
    channel: str,
    payload_path: str | None,
    reason: str,
    final_status: str,
    failure_category: str,
    dry_run: bool,
) -> dict:
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "channel": channel,
        "provider": channel,
        "payload_path": payload_path,
        "idempotency_key": None,
        "payload_size_bytes": 0,
        "final_status": final_status,
        "dispatched": False,
        "dry_run": dry_run,
        "skipped_duplicate": False,
        "attempt_count": 0,
        "http_status": None,
        "ack_status": final_status,
        "failure_category": failure_category,
        "response_text": reason,
        "security": {
            "webhook_source": "not_used",
            "signing_secret_source": "not_used",
            "url_validation": {
                "ok": channel in {"none", "stdout"},
                "category": "not_applicable",
                "message": reason,
                "host": None,
                "scheme": None,
            },
            "signed_request": False,
            "signature_mode": "none",
            "signing_secret_present": False,
        },
    }


def run_delivery(
    *,
    digest: dict,
    routes: dict,
    dispatch_policy_manifest: dict,
    event_name: str,
    default_channel: str,
    override_channel: str | None,
    dry_run: bool,
    max_attempts: int,
    retry_delay_seconds: float,
    explicit_idempotency_key: str | None,
    explicit_webhook_url: str | None,
    explicit_signing_secret: str | None,
    state_path: str | Path,
) -> dict:
    route = select_route(digest, routes, event_name, default_channel, override_channel)
    route["severity"] = digest.get("severity")
    route["headline"] = digest.get("headline")
    route["ship_ready"] = digest.get("ship_ready")
    route["failure_counts"] = digest.get("failure_counts", {})
    route["top_failure_category"] = digest.get("top_failure_category")

    dispatch_policy = evaluate_policy(digest, route, dispatch_policy_manifest, event_name)
    payload_path = route.get("payload_path")
    channel = route.get("channel", "none")

    if not dispatch_policy.get("allow_dispatch"):
        dispatch_result = build_skipped_dispatch_result(
            channel=channel,
            payload_path=payload_path,
            reason=dispatch_policy.get("reason", "dispatch suppressed by policy"),
            final_status="skipped_policy_denied",
            failure_category="policy_denied",
            dry_run=dry_run,
        )
    elif not payload_path:
        dispatch_result = build_skipped_dispatch_result(
            channel=channel,
            payload_path=payload_path,
            reason="route does not provide a payload artifact",
            final_status="missing_payload_artifact",
            failure_category="missing_payload_artifact",
            dry_run=dry_run,
        )
    else:
        payload = load_payload(payload_path)
        webhook_url = resolve_webhook_url(channel, explicit_webhook_url)
        signing_secret = resolve_signing_secret(channel, explicit_signing_secret)
        idempotency_key = build_idempotency_key(channel, payload, explicit_idempotency_key)
        dispatch_result = execute_dispatch(
            channel=channel,
            payload=payload,
            webhook_url=webhook_url,
            dry_run=dry_run,
            max_attempts=max_attempts,
            retry_delay_seconds=retry_delay_seconds,
            idempotency_key=idempotency_key,
            signing_secret=signing_secret,
            webhook_source=detect_webhook_source(channel, explicit_webhook_url),
            signing_secret_source=detect_signing_secret_source(channel, explicit_signing_secret),
            state_path=state_path,
        )
        dispatch_result["payload_path"] = payload_path

    final_status = dispatch_result.get("final_status", "unknown")
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "event_name": event_name,
        "route": route,
        "dispatch_policy": dispatch_policy,
        "dispatch_result": dispatch_result,
        "delivery_status": final_status,
        "dispatch_attempted": dispatch_policy.get("allow_dispatch", False) and bool(payload_path),
        "dispatched": bool(dispatch_result.get("dispatched")),
        "payload_path": payload_path,
    }


def format_markdown(payload: dict) -> str:
    route = payload["route"]
    dispatch_policy = payload["dispatch_policy"]
    dispatch_result = payload["dispatch_result"]
    lines = [
        "# Notification Delivery",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Event: `{payload['event_name']}`",
        f"- Channel: `{route.get('channel')}`",
        f"- Route reason: {route.get('reason')}",
        f"- Dispatch allowed: `{str(dispatch_policy.get('allow_dispatch')).lower()}`",
        f"- Dispatch policy reason: {dispatch_policy.get('reason')}",
        f"- Delivery status: `{payload.get('delivery_status')}`",
        f"- Payload path: `{payload.get('payload_path')}`",
        "",
        "## Result",
        "",
        f"- Final status: `{dispatch_result.get('final_status')}`",
        f"- Ack status: `{dispatch_result.get('ack_status')}`",
        f"- Failure category: `{dispatch_result.get('failure_category')}`",
        f"- Dispatched: `{str(dispatch_result.get('dispatched')).lower()}`",
    ]
    if route.get("matched_failure_categories"):
        lines.append(f"- Matched failure categories: `{', '.join(route['matched_failure_categories'])}`")
    if dispatch_result.get("response_text"):
        lines.extend(["", "## Response", "", "```text", str(dispatch_result["response_text"]), "```"])
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    digest = load_json(args.digest)
    routes = load_json(args.routes)
    dispatch_policy_manifest = load_json(args.dispatch_policy)
    override_channel = None if args.override_channel in {None, "", "none"} else args.override_channel
    payload = run_delivery(
        digest=digest,
        routes=routes,
        dispatch_policy_manifest=dispatch_policy_manifest,
        event_name=args.event_name,
        default_channel=args.default_channel,
        override_channel=override_channel,
        dry_run=args.dry_run,
        max_attempts=args.max_attempts,
        retry_delay_seconds=args.retry_delay_seconds,
        explicit_idempotency_key=args.idempotency_key,
        explicit_webhook_url=args.webhook_url,
        explicit_signing_secret=args.signing_secret,
        state_path=args.state_path,
    )

    print(f"channel={payload['route']['channel']}")
    print(f"allow_dispatch={str(payload['dispatch_policy']['allow_dispatch']).lower()}")
    print(f"delivery_status={payload['delivery_status']}")

    save_json(args.route_output, payload["route"])
    save_json(args.dispatch_policy_output, payload["dispatch_policy"])
    save_json(args.dispatch_result_output, payload["dispatch_result"])
    save_json(args.output, payload)

    if args.output:
        print(f"saved delivery report to {args.output}")
    if args.route_output:
        print(f"saved route report to {args.route_output}")
    if args.dispatch_policy_output:
        print(f"saved dispatch policy report to {args.dispatch_policy_output}")
    if args.dispatch_result_output:
        print(f"saved dispatch result report to {args.dispatch_result_output}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_markdown(payload), encoding="utf-8")
        print(f"saved delivery markdown to {md_output_path}")


if __name__ == "__main__":
    main()
