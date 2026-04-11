from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class MultimodalDocumentPipelineTests(unittest.TestCase):
    def test_document_pipeline_cli_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "document_pipeline.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/multimodal_eval.py",
                    "--data-path",
                    "datasets/tiny_multimodal_workflow/eval.jsonl",
                    "--strategy",
                    "document_pipeline",
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

    def test_grounded_pipeline_cli_fails_document_workflow_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "grounded_pipeline.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/multimodal_eval.py",
                    "--data-path",
                    "datasets/tiny_multimodal_workflow/eval.jsonl",
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
            self.assertIn("task_success_rate=0.000", result.stdout)


if __name__ == "__main__":
    unittest.main()
