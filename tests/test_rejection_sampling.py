from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class RejectionSamplingTests(unittest.TestCase):
    def test_rejection_sampling_improves_consensus_and_writes_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            baseline_report = tmp_path / "consensus.json"
            candidate_report = tmp_path / "rejection.json"
            accepted_output = tmp_path / "accepted.jsonl"

            baseline = subprocess.run(
                [
                    sys.executable,
                    "eval/rejection_sampling_eval.py",
                    "--data-path",
                    "datasets/tiny_reasoning_rejection/eval.jsonl",
                    "--strategy",
                    "consensus",
                    "--report-path",
                    str(baseline_report),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(baseline.returncode, 0, msg=baseline.stderr)

            candidate = subprocess.run(
                [
                    sys.executable,
                    "eval/rejection_sampling_eval.py",
                    "--data-path",
                    "datasets/tiny_reasoning_rejection/eval.jsonl",
                    "--strategy",
                    "rejection_sampling",
                    "--report-path",
                    str(candidate_report),
                    "--accepted-output",
                    str(accepted_output),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(candidate.returncode, 0, msg=candidate.stderr)
            self.assertTrue(accepted_output.exists())

            baseline_payload = json.loads(baseline_report.read_text(encoding="utf-8"))
            candidate_payload = json.loads(candidate_report.read_text(encoding="utf-8"))
            self.assertLess(baseline_payload["task_success_rate"], candidate_payload["task_success_rate"])
            self.assertEqual(candidate_payload["acceptance_rate"], 0.75)
            self.assertEqual(candidate_payload["accepted_precision"], 1.0)

            accepted_rows = [
                json.loads(line)
                for line in accepted_output.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(accepted_rows), 3)


if __name__ == "__main__":
    unittest.main()
