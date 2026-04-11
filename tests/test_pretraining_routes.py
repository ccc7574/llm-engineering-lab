from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class PretrainingRouteTests(unittest.TestCase):
    def test_train_mixture_reports_per_source_losses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "mixture"
            result = subprocess.run(
                [
                    sys.executable,
                    "code/stage1_nanogpt_core/train_mixture.py",
                    "--manifest-path",
                    "datasets/tiny_pretraining_mixture/uniform.json",
                    "--out-dir",
                    str(out_dir),
                    "--max-iters",
                    "20",
                    "--eval-interval",
                    "20",
                    "--eval-iters",
                    "5",
                    "--batch-size",
                    "8",
                    "--block-size",
                    "32",
                    "--n-embed",
                    "48",
                    "--n-head",
                    "4",
                    "--n-layer",
                    "2",
                    "--learning-rate",
                    "1e-3",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads((out_dir / "train_state.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mixture_name"], "uniform_mixture")
            self.assertIn("general", payload["source_eval_losses"])
            self.assertIn("payments", payload["source_eval_losses"])

    def test_continue_pretraining_improves_domain_loss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            base_dir = tmp_path / "base"
            adapted_dir = tmp_path / "adapted"

            base_train = subprocess.run(
                [
                    sys.executable,
                    "code/stage1_nanogpt_core/train.py",
                    "--data-path",
                    "datasets/tiny_pretraining_general/input.txt",
                    "--out-dir",
                    str(base_dir),
                    "--max-iters",
                    "20",
                    "--eval-interval",
                    "20",
                    "--eval-iters",
                    "5",
                    "--batch-size",
                    "8",
                    "--block-size",
                    "32",
                    "--n-embed",
                    "48",
                    "--n-head",
                    "4",
                    "--n-layer",
                    "2",
                    "--learning-rate",
                    "1e-3",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(base_train.returncode, 0, msg=base_train.stderr)

            adapted = subprocess.run(
                [
                    sys.executable,
                    "code/stage1_nanogpt_core/continue_pretraining.py",
                    "--checkpoint",
                    str(base_dir / "ckpt.pt"),
                    "--data-path",
                    "datasets/tiny_pretraining_payments/input.txt",
                    "--eval-set",
                    "general=datasets/tiny_pretraining_general/input.txt",
                    "--eval-set",
                    "domain=datasets/tiny_pretraining_payments/input.txt",
                    "--out-dir",
                    str(adapted_dir),
                    "--max-iters",
                    "30",
                    "--eval-interval",
                    "30",
                    "--eval-iters",
                    "5",
                    "--batch-size",
                    "8",
                    "--learning-rate",
                    "5e-4",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(adapted.returncode, 0, msg=adapted.stderr)
            payload = json.loads((adapted_dir / "train_state.json").read_text(encoding="utf-8"))
            self.assertLess(payload["adapted_eval_losses"]["domain"], payload["base_eval_losses"]["domain"])


if __name__ == "__main__":
    unittest.main()
