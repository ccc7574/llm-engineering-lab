from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class CodingPassKTests(unittest.TestCase):
    def test_sample_k_improves_pass_at_k(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "sample_k.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/coding_passk_eval.py",
                    "--data-path",
                    "datasets/tiny_coding_passk/eval.jsonl",
                    "--strategy",
                    "sample_k",
                    "--k",
                    "3",
                    "--report-path",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("pass@3=1.000", result.stdout)
            self.assertIn("avg_candidates_sampled=3.00", result.stdout)

    def test_single_sample_keeps_pass_at_k_low(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "single_sample.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/coding_passk_eval.py",
                    "--data-path",
                    "datasets/tiny_coding_passk/eval.jsonl",
                    "--strategy",
                    "single_sample",
                    "--k",
                    "3",
                    "--report-path",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("pass@3=0.000", result.stdout)
            self.assertIn("avg_candidates_sampled=1.00", result.stdout)


if __name__ == "__main__":
    unittest.main()
