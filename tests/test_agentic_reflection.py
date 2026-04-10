from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class AgenticReflectionTests(unittest.TestCase):
    def test_reflective_strategy_improves_reflection_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "reflective.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/agentic_eval.py",
                    "--data-path",
                    "datasets/tiny_agentic_reflection/eval.jsonl",
                    "--strategy",
                    "reflective",
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
            self.assertIn("avg_reflection_steps=1.00", result.stdout)

    def test_tool_use_strategy_fails_reflection_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "tool_use.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/agentic_eval.py",
                    "--data-path",
                    "datasets/tiny_agentic_reflection/eval.jsonl",
                    "--strategy",
                    "tool_use",
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
