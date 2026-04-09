from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-report", required=True)
    parser.add_argument("--candidate-report", required=True)
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def load_report(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def numeric_summary(report: dict) -> dict[str, float]:
    summary = {}
    for key, value in report.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            summary[key] = float(value)
    return summary


def main() -> None:
    args = parse_args()
    baseline = load_report(args.baseline_report)
    candidate = load_report(args.candidate_report)

    baseline_summary = numeric_summary(baseline)
    candidate_summary = numeric_summary(candidate)
    shared_keys = sorted(set(baseline_summary) & set(candidate_summary))

    deltas = {}
    print("metric\tbaseline\tcandidate\tdelta")
    for key in shared_keys:
        baseline_value = baseline_summary[key]
        candidate_value = candidate_summary[key]
        delta = candidate_value - baseline_value
        deltas[key] = delta
        print(f"{key}\t{baseline_value:.3f}\t{candidate_value:.3f}\t{delta:+.3f}")

    payload = {
        "baseline_report": args.baseline_report,
        "candidate_report": args.candidate_report,
        "deltas": deltas,
    }

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved regression diff to {output_path}")


if __name__ == "__main__":
    main()
