from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class Stage5ToyAlignmentTests(unittest.TestCase):
    def test_stage5_scripts_compile(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "py_compile",
                "code/stage5_toy_alignment/__init__.py",
                "code/stage5_toy_alignment/dataset.py",
                "code/stage5_toy_alignment/utils.py",
                "code/stage5_toy_alignment/train_dpo.py",
                "code/stage5_toy_alignment/train_grpo.py",
                "eval/alignment_eval.py",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_stage5_dpo_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "code/stage5_toy_alignment/train_dpo.py",
                    "--data-path",
                    "datasets/tiny_preferences/train.jsonl",
                    "--init-from",
                    "runs/stage2_sft_smoke/ckpt.pt",
                    "--out-dir",
                    str(Path(tmp_dir) / "stage5_dpo"),
                    "--max-iters",
                    "1",
                    "--eval-interval",
                    "1",
                    "--batch-size",
                    "2",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("pair_count=4", result.stdout)

    def test_stage5_grpo_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "code/stage5_toy_alignment/train_grpo.py",
                    "--data-path",
                    "datasets/tiny_preferences/train.jsonl",
                    "--init-from",
                    "runs/stage2_sft_smoke/ckpt.pt",
                    "--out-dir",
                    str(Path(tmp_dir) / "stage5_grpo"),
                    "--max-iters",
                    "1",
                    "--eval-interval",
                    "1",
                    "--batch-size",
                    "2",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("pair_count=4", result.stdout)


if __name__ == "__main__":
    unittest.main()
