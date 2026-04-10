from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


DEFAULT_MARKER = "<!-- llm-engineering-lab:release-note -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--body-path", required=True)
    parser.add_argument("--token", default=None)
    parser.add_argument("--api-base", default="https://api.github.com")
    parser.add_argument("--marker", default=DEFAULT_MARKER)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-failure", action="store_true")
    parser.add_argument("--skip-if-missing-token", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def load_body(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def resolve_token(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def detect_token_source(explicit: str | None) -> str:
    if explicit:
        return "argument"
    if os.environ.get("GH_TOKEN"):
        return "GH_TOKEN"
    if os.environ.get("GITHUB_TOKEN"):
        return "GITHUB_TOKEN"
    return "missing"


def build_comment_body(marker: str, body: str) -> str:
    stripped = body.lstrip()
    if stripped.startswith(marker):
        return body
    return f"{marker}\n\n{body}"


def extract_api_message(response_text: str) -> str:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError:
        return response_text.strip()
    if isinstance(payload, dict):
        return str(payload.get("message") or payload.get("error") or response_text).strip()
    return response_text.strip()


def diagnose_api_failure(status_code: int | None, response_text: str, phase: str) -> dict:
    message = extract_api_message(response_text)
    lowered = message.lower()
    if status_code == 401:
        category = "invalid_token"
        hint = "Check whether GITHUB_TOKEN or GH_TOKEN is present, valid, and not expired."
    elif status_code == 403 and "resource not accessible by integration" in lowered:
        category = "insufficient_permission"
        hint = "Grant `issues: write` and `pull-requests: write`, or run the workflow in a context where the token can write PR comments."
    elif status_code == 403:
        category = "forbidden"
        hint = "Check repo policy, token scope, and whether this run comes from a fork or restricted automation context."
    elif status_code == 404:
        category = "repo_or_pr_not_found"
        hint = "Check repo name, PR number, and whether the token can access the target repository and pull request."
    elif status_code == 422:
        category = "validation_failed"
        hint = "Check whether the PR is open and whether the comment payload is valid for the GitHub Issues Comments API."
    else:
        category = "api_error"
        hint = "Inspect the raw GitHub API response and confirm network reachability, token scope, and request payload."
    return {
        "phase": phase,
        "category": category,
        "message": message,
        "actionable_hint": hint,
    }


def format_pr_comment_result_markdown(result: dict) -> str:
    lines = [
        "# PR Comment Result",
        "",
        f"- Generated at: {result.get('generated_at', 'unknown')}",
        f"- Final Status: {result.get('final_status', 'unknown')}",
        f"- Comment Action: {result.get('comment_action', 'unknown')}",
        f"- Token Source: {result.get('token_source', 'missing')}",
        f"- Token Present: {str(bool(result.get('token_present'))).lower()}",
    ]
    if result.get("comment_id") is not None:
        lines.append(f"- Comment ID: {result['comment_id']}")
    if result.get("comment_url"):
        lines.append(f"- Comment URL: {result['comment_url']}")
    diagnosis = result.get("diagnosis")
    if diagnosis:
        lines.extend(
            [
                f"- Diagnosis: {diagnosis.get('category', 'unknown')} ({diagnosis.get('phase', 'unknown')})",
                f"- API Message: {diagnosis.get('message', '')}",
                f"- Actionable Hint: {diagnosis.get('actionable_hint', '')}",
            ]
        )
    return "\n".join(lines) + "\n"


def api_request(
    url: str,
    token: str,
    method: str = "GET",
    payload: dict | None = None,
) -> tuple[int, str]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "llm-engineering-lab-pr-comment",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            return response.getcode(), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def find_existing_comment(comments: list[dict], marker: str) -> dict | None:
    for comment in comments:
        body = comment.get("body", "")
        if marker in body:
            return comment
    return None


def publish_pr_comment(
    *,
    repo: str,
    pr_number: int,
    body: str,
    token: str | None,
    token_source: str = "missing",
    api_base: str,
    marker: str,
    dry_run: bool,
    allow_failure: bool,
    skip_if_missing_token: bool,
) -> dict:
    comment_body = build_comment_body(marker, body)
    effective_token_source = token_source
    if token and token_source == "missing":
        effective_token_source = "provided"
    base_payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "repo": repo,
        "pr_number": pr_number,
        "marker": marker,
        "dry_run": dry_run,
        "token_source": effective_token_source,
        "token_present": bool(token),
    }

    if dry_run:
        return {
            **base_payload,
            "final_status": "dry_run",
            "comment_action": "dry_run",
            "comment_id": None,
            "response_code": None,
            "response_text": comment_body,
            "diagnosis": None,
        }

    if not token:
        result = {
            **base_payload,
            "final_status": "missing_token",
            "comment_action": "skipped",
            "comment_id": None,
            "response_code": None,
            "response_text": "missing GitHub token",
            "diagnosis": {
                "phase": "preflight",
                "category": "missing_token",
                "message": "missing GitHub token",
                "actionable_hint": "Provide `GITHUB_TOKEN`, `GH_TOKEN`, or pass `--token` when PR comment writeback is expected.",
            },
        }
        if skip_if_missing_token or allow_failure:
            return result
        raise SystemExit("missing GitHub token")

    comments_url = f"{api_base}/repos/{repo}/issues/{pr_number}/comments?per_page=100"
    status_code, response_text = api_request(comments_url, token, method="GET")
    if status_code != 200:
        result = {
            **base_payload,
            "final_status": "list_failed",
            "comment_action": "failed",
            "comment_id": None,
            "response_code": status_code,
            "response_text": response_text,
            "diagnosis": diagnose_api_failure(status_code, response_text, "list_comments"),
        }
        if allow_failure:
            return result
        raise SystemExit(f"failed to list PR comments: {status_code} {response_text}")

    comments = json.loads(response_text)
    existing = find_existing_comment(comments, marker)
    if existing:
        comment_id = existing["id"]
        update_url = f"{api_base}/repos/{repo}/issues/comments/{comment_id}"
        status_code, response_text = api_request(update_url, token, method="PATCH", payload={"body": comment_body})
        success_codes = {200}
        action = "updated"
    else:
        create_url = f"{api_base}/repos/{repo}/issues/{pr_number}/comments"
        status_code, response_text = api_request(create_url, token, method="POST", payload={"body": comment_body})
        success_codes = {201}
        action = "created"
        comment_id = None

    if status_code not in success_codes:
        result = {
            **base_payload,
            "final_status": "publish_failed",
            "comment_action": action,
            "comment_id": comment_id,
            "response_code": status_code,
            "response_text": response_text,
            "diagnosis": diagnose_api_failure(status_code, response_text, "publish_comment"),
        }
        if allow_failure:
            return result
        raise SystemExit(f"failed to publish PR comment: {status_code} {response_text}")

    payload = json.loads(response_text)
    return {
        **base_payload,
        "final_status": "published",
        "comment_action": action,
        "comment_id": payload.get("id"),
        "comment_url": payload.get("html_url"),
        "response_code": status_code,
        "response_text": "published",
        "diagnosis": None,
    }


def main() -> None:
    args = parse_args()
    body = load_body(args.body_path)
    token = resolve_token(args.token)
    token_source = detect_token_source(args.token)
    result = publish_pr_comment(
        repo=args.repo,
        pr_number=args.pr_number,
        body=body,
        token=token,
        token_source=token_source,
        api_base=args.api_base,
        marker=args.marker,
        dry_run=args.dry_run,
        allow_failure=args.allow_failure,
        skip_if_missing_token=args.skip_if_missing_token,
    )

    print(f"final_status={result['final_status']}")
    print(f"comment_action={result['comment_action']}")
    if result.get("comment_id") is not None:
        print(f"comment_id={result['comment_id']}")
    if result.get("comment_url"):
        print(f"comment_url={result['comment_url']}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved PR comment result to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_pr_comment_result_markdown(result), encoding="utf-8")
        print(f"saved PR comment markdown result to {md_output_path}")

    if result["final_status"] in {"list_failed", "publish_failed"} and not args.allow_failure:
        sys.exit(1)
    if result["final_status"] == "missing_token" and not (args.skip_if_missing_token or args.allow_failure):
        sys.exit(2)


if __name__ == "__main__":
    main()
