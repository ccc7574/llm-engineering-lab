from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from code.stage_harness.notification_dispatch_policy import evaluate_policy
from code.stage_harness.notification_review_summary import build_summary, format_markdown


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


if __name__ == "__main__":
    unittest.main()
