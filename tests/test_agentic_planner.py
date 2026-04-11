from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class AgenticPlannerObserverTests(unittest.TestCase):
    def test_planner_observer_strategy_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "planner_observer.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/agentic_eval.py",
                    "--data-path",
                    "datasets/tiny_agentic_planner/eval.jsonl",
                    "--strategy",
                    "planner_observer",
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
            self.assertIn("avg_observer_checks=2.00", result.stdout)

    def test_stateful_strategy_fails_planner_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "stateful.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "eval/agentic_eval.py",
                    "--data-path",
                    "datasets/tiny_agentic_planner/eval.jsonl",
                    "--strategy",
                    "stateful",
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
