from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class SwebenchLiteTests(unittest.TestCase):
    def test_triage_loop_cli_solves_swebench_lite_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "triage_loop.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/swebench_eval.py",
                    "--data-path",
                    "datasets/tiny_swebench_lite/eval.jsonl",
                    "--strategy",
                    "triage_loop",
                    "--report-path",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("task_success_rate=1.000", result.stdout)
            self.assertIn("avg_triage_reads=1.00", result.stdout)

    def test_issue_localized_cli_fails_swebench_lite_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "issue_localized.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/swebench_eval.py",
                    "--data-path",
                    "datasets/tiny_swebench_lite/eval.jsonl",
                    "--strategy",
                    "issue_localized",
                    "--report-path",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("task_success_rate=0.000", result.stdout)
            self.assertIn("avg_patch_recall=0.50", result.stdout)


if __name__ == "__main__":
    unittest.main()
