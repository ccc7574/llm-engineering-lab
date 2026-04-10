from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import urllib.error

from code.stage_harness.notification_dispatch import (
    build_idempotency_key,
    classify_dispatch_response,
    execute_dispatch,
)
from code.stage_harness.notification_route import select_route
from code.stage_harness.notification_route_lint import lint_routes
from code.stage_harness.pr_comment import (
    build_comment_body,
    diagnose_api_failure,
    find_existing_comment,
    format_pr_comment_result_markdown,
    publish_pr_comment,
)
from code.stage_harness.notification_dispatch_policy import evaluate_policy
from code.stage_harness.release_note import build_release_note, format_markdown as format_release_note_markdown
from code.stage_harness.notification_review_summary import build_summary, format_markdown
from code.stage_harness.trend_board import build_trend_board


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_GATE_SCRIPT = REPO_ROOT / "code/stage_harness/notification_policy_gate.py"
DISPATCH_POLICY_MANIFEST = REPO_ROOT / "manifests/notification_dispatch_policy.json"


class NotificationHarnessTests(unittest.TestCase):
    def test_policy_gate_report_mode_does_not_fail_on_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            route_diff_path = tmp_path / "route_diff.json"
            policy_path = tmp_path / "policy_gate.json"
            output_path = tmp_path / "policy_gate_report.json"

            route_diff_path.write_text(
                json.dumps(
                    {
                        "diffs": [
                            {
                                "event_name": "workflow_dispatch",
                                "severity": "warning",
                                "gate": "hold",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            policy_path.write_text(
                json.dumps({"max_changed_rows": 1, "allowed_changes": []}),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(POLICY_GATE_SCRIPT),
                    "--route-diff",
                    str(route_diff_path),
                    "--policy",
                    str(policy_path),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["decision"], "hold")

    def test_policy_gate_fail_mode_exits_non_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            route_diff_path = tmp_path / "route_diff.json"
            policy_path = tmp_path / "policy_gate.json"

            route_diff_path.write_text(
                json.dumps(
                    {
                        "diffs": [
                            {
                                "event_name": "workflow_dispatch",
                                "severity": "warning",
                                "gate": "hold",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            policy_path.write_text(
                json.dumps({"max_changed_rows": 1, "allowed_changes": []}),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(POLICY_GATE_SCRIPT),
                    "--route-diff",
                    str(route_diff_path),
                    "--policy",
                    str(policy_path),
                    "--fail-on-non-ship",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)

    def test_dispatch_policy_allows_schedule_dispatch(self) -> None:
        digest = {
            "severity": "info",
            "overall_gate": "ship",
            "ship_ready": True,
        }
        route = {
            "channel": "slack_webhook",
            "payload_path": "runs/notification_slack.json",
            "override_applied": False,
        }
        policy = json.loads(DISPATCH_POLICY_MANIFEST.read_text(encoding="utf-8"))

        payload = evaluate_policy(digest, route, policy, "schedule")

        self.assertTrue(payload["allow_dispatch"])
        self.assertEqual(payload["matched_rule"], "scheduled_dispatch")

    def test_dispatch_policy_suppresses_manual_default_route(self) -> None:
        digest = {
            "severity": "info",
            "overall_gate": "ship",
            "ship_ready": True,
        }
        route = {
            "channel": "slack_webhook",
            "payload_path": "runs/notification_slack.json",
            "override_applied": False,
        }
        policy = json.loads(DISPATCH_POLICY_MANIFEST.read_text(encoding="utf-8"))

        payload = evaluate_policy(digest, route, policy, "workflow_dispatch")

        self.assertFalse(payload["allow_dispatch"])
        self.assertEqual(payload["decision"], "skip")

    def test_route_matches_failure_category_specific_rule(self) -> None:
        digest = {
            "severity": "warning",
            "overall_gate": "hold",
            "ship_ready": False,
            "failure_counts": {"permission_error": 1},
            "top_failure_category": "permission_error",
        }
        routes = {
            "channel_payloads": {"none": None, "feishu_webhook": "runs/notification_feishu.json"},
            "rules": [
                {
                    "event_names": ["workflow_dispatch"],
                    "severities": ["warning", "critical"],
                    "gates": ["hold", "block"],
                    "failure_categories": ["permission_error"],
                    "channel": "feishu_webhook",
                    "reason": "manual runs with infra failures route to feishu",
                }
            ],
        }

        route = select_route(
            digest=digest,
            routes=routes,
            event_name="workflow_dispatch",
            default_channel="none",
            override_channel=None,
        )

        self.assertEqual(route["channel"], "feishu_webhook")
        self.assertEqual(route["matched_failure_categories"], ["permission_error"])

    def test_route_lint_warns_on_unknown_failure_category(self) -> None:
        issues = lint_routes(
            {
                "channel_payloads": {"none": None, "slack_webhook": "runs/notification_slack.json"},
                "rules": [
                    {
                        "event_names": ["workflow_dispatch"],
                        "failure_categories": ["mystery_failure"],
                        "channel": "slack_webhook",
                        "reason": "test rule",
                    }
                ],
            }
        )

        self.assertTrue(any(issue["type"] == "unknown_failure_category" for issue in issues))

    def test_review_summary_surfaces_suppressed_dispatch(self) -> None:
        digest = {
            "headline": "Regression suite needs attention",
            "severity": "warning",
            "suite_status": "passed",
            "overall_gate": "hold",
            "ship_ready": False,
            "active_scopes": ["harness"],
            "failed_steps": [{"name": "route_policy_gate"}],
            "failure_counts": {"logic_error": 1},
        }
        route = {
            "event_name": "workflow_dispatch",
            "channel": "slack_webhook",
            "reason": "no routing rule matched",
            "override_applied": False,
        }
        policy_gate = {
            "decision": "hold",
            "reason": "route diff contains unexpected event/severity/gate changes",
            "changed_rows": 2,
        }
        dispatch_policy = {
            "allow_dispatch": False,
            "reason": "default deny for non-scheduled events to avoid noisy live notifications",
            "matched_rule": None,
        }

        summary = build_summary(digest, route, policy_gate, dispatch_policy)
        markdown = format_markdown(summary)

        self.assertFalse(summary["dispatch_allowed"])
        self.assertIn("suppressed by dispatch policy", "\n".join(summary["reviewer_notes"]))
        self.assertIn("Dispatch allowed: false", markdown)

    def test_trend_board_compares_snapshot_drift(self) -> None:
        summary_board = {
            "runs_dir": "runs",
            "rows": [
                {
                    "track_key": "agentic",
                    "label": "Agentic",
                    "status": "passed",
                    "primary_metric": "task_success_rate",
                    "quality_delta": 1.0,
                    "cost_signals": [{"metric": "avg_steps", "delta": 1.0}],
                }
            ],
        }
        suite_report = {
            "manifest": "manifests/regression_v2_suite.json",
            "run_mode": "full",
            "overall_status": "passed",
            "release_decision": "ship",
            "steps_total": 2,
            "steps_passed": 2,
            "results": [
                {"name": "step_a", "status": "passed", "duration_seconds": 1.2, "attempt_count": 1},
                {"name": "step_b", "status": "passed", "duration_seconds": 0.4, "attempt_count": 1},
            ],
        }
        baseline_snapshot = {
            "suite": {
                "total_duration_seconds": 1.0,
                "slowest_steps": [{"name": "step_a", "duration_seconds": 0.7, "status": "passed", "attempt_count": 1}],
            },
            "tracks": [
                {
                    "track_key": "agentic",
                    "label": "Agentic",
                    "quality_delta": 0.5,
                    "cost_signals": {"avg_steps": 0.2},
                }
            ],
        }

        payload = build_trend_board(
            summary_board=summary_board,
            suite_report=suite_report,
            baseline_snapshot=baseline_snapshot,
            top_steps=3,
            top_drifts=5,
        )

        self.assertTrue(payload["baseline_snapshot_present"])
        self.assertGreater(payload["comparison"]["suite_duration_delta_seconds"], 0)
        self.assertEqual(payload["comparison"]["track_cost_drifts"][0]["metric"], "avg_steps")

    def test_dispatch_retries_then_succeeds(self) -> None:
        payload = {"text": "hello"}
        responses = [
            urllib.error.URLError("temporary network failure"),
            mock.Mock(
                __enter__=mock.Mock(
                    return_value=mock.Mock(
                        getcode=mock.Mock(return_value=200),
                        read=mock.Mock(return_value=b"ok"),
                        headers={},
                    )
                ),
                __exit__=mock.Mock(return_value=False),
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch(
            "code.stage_harness.notification_dispatch.urllib.request.urlopen",
            side_effect=responses,
        ), mock.patch("code.stage_harness.notification_dispatch.time.sleep") as sleep_mock:
            result = execute_dispatch(
                channel="slack_webhook",
                payload=payload,
                webhook_url="https://example.invalid/webhook",
                dry_run=False,
                max_attempts=2,
                retry_delay_seconds=0.1,
                idempotency_key=build_idempotency_key("slack_webhook", payload, None),
                state_path=Path(tmp_dir) / "dispatch_state.json",
            )

        self.assertTrue(result["dispatched"])
        self.assertEqual(result["attempt_count"], 2)
        sleep_mock.assert_called_once()

    def test_dispatch_skips_duplicate_after_success(self) -> None:
        payload = {"text": "duplicate"}
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "dispatch_state.json"
            idempotency_key = build_idempotency_key("slack_webhook", payload, None)
            with mock.patch(
                "code.stage_harness.notification_dispatch.urllib.request.urlopen",
                return_value=mock.Mock(
                    __enter__=mock.Mock(
                        return_value=mock.Mock(
                            getcode=mock.Mock(return_value=200),
                            read=mock.Mock(return_value=b"ok"),
                            headers={},
                        )
                    ),
                    __exit__=mock.Mock(return_value=False),
                ),
            ):
                first = execute_dispatch(
                    channel="slack_webhook",
                    payload=payload,
                    webhook_url="https://example.invalid/webhook",
                    dry_run=False,
                    max_attempts=1,
                    retry_delay_seconds=0.0,
                    idempotency_key=idempotency_key,
                    state_path=state_path,
                )

            second = execute_dispatch(
                channel="slack_webhook",
                payload=payload,
                webhook_url="https://example.invalid/webhook",
                dry_run=False,
                max_attempts=1,
                retry_delay_seconds=0.0,
                idempotency_key=idempotency_key,
                state_path=state_path,
            )

        self.assertEqual(first["final_status"], "dispatched")
        self.assertEqual(second["final_status"], "skipped_duplicate")
        self.assertTrue(second["skipped_duplicate"])

    def test_provider_ack_classifies_slack_permanent_rejection(self) -> None:
        classification = classify_dispatch_response(
            channel="slack_webhook",
            http_status=404,
            response_text="channel_not_found",
            headers={},
        )

        self.assertEqual(classification["ack_status"], "rejected")
        self.assertEqual(classification["failure_category"], "permanent_rejection")
        self.assertFalse(classification["retryable"])

    def test_provider_ack_classifies_feishu_json_success(self) -> None:
        classification = classify_dispatch_response(
            channel="feishu_webhook",
            http_status=200,
            response_text=json.dumps({"code": 0, "msg": "success"}),
            headers={},
        )

        self.assertEqual(classification["ack_status"], "ok")
        self.assertEqual(classification["failure_category"], "success")
        self.assertFalse(classification["retryable"])

    def test_release_note_rolls_up_core_artifacts(self) -> None:
        summary_board = {
            "rows": [
                {
                    "label": "Agentic",
                    "status": "passed",
                    "primary_metric": "task_success_rate",
                    "quality_delta": 1.0,
                },
                {
                    "label": "Coding Repo Context",
                    "status": "flat",
                    "primary_metric": "pass_at_1",
                    "quality_delta": 0.0,
                },
            ]
        }
        suite_report = {
            "overall_status": "passed",
            "steps_passed": 36,
            "steps_total": 36,
        }
        digest = {"headline": "Regression suite passed", "active_scopes": ["harness"]}
        review_summary = {
            "headline": "Regression suite passed",
            "ship_ready": True,
            "policy_gate_decision": "ship",
            "overall_gate": "ship",
            "event_name": "schedule",
            "failed_steps": [],
            "reviewer_notes": ["Regression suite is ship-ready from the current suite and release gate perspective."],
        }
        trend_board = {
            "current_snapshot": {
                "suite": {
                    "total_duration_seconds": 14.0,
                    "slowest_steps": [{"name": "agentic_tool_use", "duration_seconds": 0.66, "status": "passed", "attempt_count": 1}],
                }
            },
            "comparison": {
                "suite_duration_delta_seconds": 1.2,
                "track_cost_drifts": [
                    {
                        "label": "Agentic",
                        "metric": "avg_steps",
                        "baseline_delta": 0.2,
                        "current_delta": 1.0,
                        "drift": 0.8,
                    }
                ],
            },
        }
        dispatch_result = {"final_status": "dry_run"}

        payload = build_release_note(
            summary_board=summary_board,
            suite_report=suite_report,
            digest=digest,
            review_summary=review_summary,
            trend_board=trend_board,
            dispatch_result=dispatch_result,
        )
        markdown = format_release_note_markdown(payload)

        self.assertEqual(payload["release_status"], "ready")
        self.assertEqual(payload["dispatch_status"], "dry_run")
        self.assertIn("Reviewer Checklist", markdown)
        self.assertIn("Cost Drift", markdown)

    def test_pr_comment_body_is_marker_prefixed(self) -> None:
        body = build_comment_body("<!-- marker -->", "# Title")
        self.assertTrue(body.startswith("<!-- marker -->"))

    def test_pr_comment_finds_existing_marker_comment(self) -> None:
        comment = find_existing_comment(
            [
                {"id": 1, "body": "hello"},
                {"id": 2, "body": "<!-- llm-engineering-lab:release-note -->\n\ncontent"},
            ],
            "<!-- llm-engineering-lab:release-note -->",
        )
        self.assertEqual(comment["id"], 2)

    def test_pr_comment_missing_token_can_skip(self) -> None:
        result = publish_pr_comment(
            repo="octo/repo",
            pr_number=12,
            body="# Release Candidate Ready",
            token=None,
            api_base="https://api.github.com",
            marker="<!-- marker -->",
            dry_run=False,
            allow_failure=False,
            skip_if_missing_token=True,
        )
        self.assertEqual(result["final_status"], "missing_token")
        self.assertEqual(result["diagnosis"]["category"], "missing_token")

    def test_pr_comment_dry_run_returns_body(self) -> None:
        result = publish_pr_comment(
            repo="octo/repo",
            pr_number=12,
            body="# Release Candidate Ready",
            token="token",
            api_base="https://api.github.com",
            marker="<!-- marker -->",
            dry_run=True,
            allow_failure=False,
            skip_if_missing_token=False,
        )
        self.assertEqual(result["final_status"], "dry_run")
        self.assertIn("Release Candidate Ready", result["response_text"])

    def test_pr_comment_diagnoses_permission_failure(self) -> None:
        diagnosis = diagnose_api_failure(
            403,
            json.dumps({"message": "Resource not accessible by integration"}),
            "publish_comment",
        )
        self.assertEqual(diagnosis["category"], "insufficient_permission")
        self.assertIn("pull-requests: write", diagnosis["actionable_hint"])

    def test_pr_comment_markdown_includes_diagnosis(self) -> None:
        markdown = format_pr_comment_result_markdown(
            {
                "generated_at": "2026-04-10T22:30:00+08:00",
                "final_status": "publish_failed",
                "comment_action": "created",
                "token_source": "GITHUB_TOKEN",
                "token_present": True,
                "diagnosis": {
                    "phase": "publish_comment",
                    "category": "insufficient_permission",
                    "message": "Resource not accessible by integration",
                    "actionable_hint": "Grant permissions.",
                },
            }
        )
        self.assertIn("PR Comment Result", markdown)
        self.assertIn("insufficient_permission", markdown)
        self.assertIn("Grant permissions.", markdown)


if __name__ == "__main__":
    unittest.main()
