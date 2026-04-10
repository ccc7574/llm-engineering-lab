from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class MultimodalGroundingTests(unittest.TestCase):
    def test_grounded_pipeline_cli_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "grounded.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/multimodal_eval.py",
                    "--data-path",
                    "datasets/tiny_multimodal_grounding/eval.jsonl",
                    "--strategy",
                    "grounded_pipeline",
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

    def test_ocr_only_cli_fails_grounding_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "ocr.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/multimodal_eval.py",
                    "--data-path",
                    "datasets/tiny_multimodal_grounding/eval.jsonl",
                    "--strategy",
                    "ocr_only",
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


if __name__ == "__main__":
    unittest.main()
