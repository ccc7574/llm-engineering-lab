from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class MultimodalSftTests(unittest.TestCase):
    def test_multimodal_route_sft_improves_router_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            train_dir = tmp_path / "multimodal_sft_router"
            baseline_report = tmp_path / "heuristic_router.json"
            candidate_report = tmp_path / "learned_router.json"

            train = subprocess.run(
                [
                    sys.executable,
                    "code/stage_multimodal/train_multimodal_sft.py",
                    "--data-path",
                    "datasets/tiny_multimodal_sft/train.jsonl",
                    "--out-dir",
                    str(train_dir),
                    "--max-iters",
                    "200",
                    "--eval-interval",
                    "50",
                    "--learning-rate",
                    "0.2",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(train.returncode, 0, msg=train.stderr)
            self.assertIn("route_accuracy=1.000", train.stdout)

            baseline = subprocess.run(
                [
                    sys.executable,
                    "eval/multimodal_sft_eval.py",
                    "--data-path",
                    "datasets/tiny_multimodal_sft/eval.jsonl",
                    "--strategy",
                    "heuristic_router",
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
                    "eval/multimodal_sft_eval.py",
                    "--data-path",
                    "datasets/tiny_multimodal_sft/eval.jsonl",
                    "--strategy",
                    "learned_router",
                    "--checkpoint",
                    str(train_dir / "router.pt"),
                    "--report-path",
                    str(candidate_report),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(candidate.returncode, 0, msg=candidate.stderr)

            baseline_payload = json.loads(baseline_report.read_text(encoding="utf-8"))
            candidate_payload = json.loads(candidate_report.read_text(encoding="utf-8"))
            self.assertLess(baseline_payload["task_success_rate"], candidate_payload["task_success_rate"])
            self.assertLess(baseline_payload["route_accuracy"], candidate_payload["route_accuracy"])
            self.assertEqual(candidate_payload["task_success_rate"], 1.0)
            self.assertEqual(candidate_payload["route_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
