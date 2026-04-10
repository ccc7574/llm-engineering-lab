from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256_text(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


class ArtifactGovernanceTests(unittest.TestCase):
    def test_artifact_catalog_cli_classifies_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            runs_dir = root / "runs"
            runs_dir.mkdir()
            (runs_dir / "regression_suite_report.json").write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "coding_eval_weak",
                                "status": "passed",
                                "command": ["python3", "eval/coding_eval.py"],
                                "expected_outputs": ["runs/coding_eval_weak.json"],
                                "missing_outputs": [],
                                "failure_category": None,
                                "failure_summary": None,
                                "stdout_excerpt": "",
                                "stderr_excerpt": "",
                                "duration_seconds": 0.1,
                                "return_code": 0,
                                "attempt_count": 1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (runs_dir / "coding_eval_weak.json").write_text('{"pass_at_1": 0.0}', encoding="utf-8")
            (runs_dir / "summary_board.json").write_text('{"rows": []}', encoding="utf-8")
            (runs_dir / "gate_report.json").write_text('{"overall_gate": "ship"}', encoding="utf-8")
            output_path = root / "artifact_catalog.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "code/stage_harness/artifact_catalog.py"),
                    "--runs-dir",
                    str(runs_dir),
                    "--manifest",
                    str(REPO_ROOT / "manifests/regression_v2_suite.json"),
                    "--policy-path",
                    str(REPO_ROOT / "manifests/artifact_lifecycle_policy.json"),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["lifecycle_counts"]["promote_on_ship"], 3)
            self.assertEqual(payload["lifecycle_counts"]["retain_for_replay"], 1)

    def test_baseline_snapshot_cli_copies_promoted_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_file = root / "summary_board.json"
            source_file.write_text('{"rows": []}', encoding="utf-8")
            catalog_path = root / "catalog.json"
            catalog_path.write_text(
                json.dumps(
                    {
                        "rows": [
                            {
                                "path": "runs/summary_board.json",
                                "source_path": str(source_file),
                                "category": "summary_board",
                                "lifecycle": "promote_on_ship",
                                "sha256": sha256_text(source_file),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output_root = root / "artifacts" / "baselines"

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "code/stage_harness/baseline_snapshot.py"),
                    "--catalog",
                    str(catalog_path),
                    "--label",
                    "ship-ready-v1",
                    "--output-root",
                    str(output_root),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            manifest = json.loads((output_root / "ship-ready-v1" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["files_copied"], 1)
            self.assertTrue(manifest["rows"][0]["hash_verified"])

    def test_failure_replay_cli_emits_failed_step_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            suite_report = root / "suite.json"
            suite_report.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "coding_eval_weak",
                                "status": "failed",
                                "command": ["python3", "eval/coding_eval.py", "--strategy", "weak"],
                                "failure_category": "test_failure",
                                "failure_summary": "tests failed",
                                "missing_outputs": [],
                                "stdout_excerpt": "reverse_string: fail\npass@1=0.000",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output_path = root / "failure_replay_plan.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "code/stage_harness/failure_replay.py"),
                    "--suite-report",
                    str(suite_report),
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["failed_step_count"], 1)
            self.assertEqual(payload["rows"][0]["failed_items"], ["reverse_string"])


if __name__ == "__main__":
    unittest.main()
