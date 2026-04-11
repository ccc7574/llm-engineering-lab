from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class AlignmentEvalTests(unittest.TestCase):
    def test_alignment_eval_reports_dpo_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            train_dir = tmp_path / "stage5_dpo"
            baseline_report = tmp_path / "baseline.json"
            candidate_report = tmp_path / "candidate.json"

            train_result = subprocess.run(
                [
                    sys.executable,
                    "code/stage5_toy_alignment/train_dpo.py",
                    "--data-path",
                    "datasets/tiny_preferences/train.jsonl",
                    "--init-from",
                    "runs/stage2_sft_smoke/ckpt.pt",
                    "--out-dir",
                    str(train_dir),
                    "--max-iters",
                    "20",
                    "--eval-interval",
                    "20",
                    "--batch-size",
                    "2",
                    "--learning-rate",
                    "5e-4",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(train_result.returncode, 0, msg=train_result.stderr)

            baseline_result = subprocess.run(
                [
                    sys.executable,
                    "eval/alignment_eval.py",
                    "--checkpoint",
                    "runs/stage2_sft_smoke/ckpt.pt",
                    "--reference-checkpoint",
                    "runs/stage2_sft_smoke/ckpt.pt",
                    "--data-path",
                    "datasets/tiny_preferences/train.jsonl",
                    "--report-path",
                    str(baseline_report),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(baseline_result.returncode, 0, msg=baseline_result.stderr)

            candidate_result = subprocess.run(
                [
                    sys.executable,
                    "eval/alignment_eval.py",
                    "--checkpoint",
                    str(train_dir / "ckpt.pt"),
                    "--reference-checkpoint",
                    "runs/stage2_sft_smoke/ckpt.pt",
                    "--data-path",
                    "datasets/tiny_preferences/train.jsonl",
                    "--report-path",
                    str(candidate_report),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(candidate_result.returncode, 0, msg=candidate_result.stderr)

            baseline = json.loads(baseline_report.read_text(encoding="utf-8"))
            candidate = json.loads(candidate_report.read_text(encoding="utf-8"))
            self.assertGreater(candidate["mean_preference_margin"], baseline["mean_preference_margin"])
            self.assertLess(candidate["dpo_loss"], baseline["dpo_loss"])


if __name__ == "__main__":
    unittest.main()
