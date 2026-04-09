from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class GateDecision:
    label: str
    status: str
    primary_metric: str
    delta: float
    gate: float
    decision: str
    reason: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-board", default="runs/summary_board.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--allow-flat", action="store_true")
    return parser.parse_args()


def load_summary(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def decide_row(row: dict, allow_flat: bool) -> GateDecision:
    status = row["status"]
    label = row["label"]
    metric = row["primary_metric"]
    delta = float(row["quality_delta"])
    gate = float(row["quality_gate"])

    if status == "regressed":
        return GateDecision(label, status, metric, delta, gate, "block", "quality regressed below baseline")
    if status == "flat" and not allow_flat:
        return GateDecision(label, status, metric, delta, gate, "hold", "quality gain did not clear promotion gate")
    return GateDecision(label, status, metric, delta, gate, "ship", "quality gate cleared")


def main() -> None:
    args = parse_args()
    summary = load_summary(args.summary_board)
    decisions = [decide_row(row, args.allow_flat) for row in summary.get("rows", [])]

    overall = "ship"
    if any(decision.decision == "block" for decision in decisions):
        overall = "block"
    elif any(decision.decision == "hold" for decision in decisions):
        overall = "hold"

    print("track\tstatus\tdelta\tdecision\treason")
    for decision in decisions:
        print(
            f"{decision.label}\t{decision.status}\t{decision.delta:+.3f}\t"
            f"{decision.decision}\t{decision.reason}"
        )
    print(f"overall_gate={overall}")

    payload = {
        "summary_board": str(args.summary_board),
        "overall_gate": overall,
        "allow_flat": args.allow_flat,
        "decisions": [asdict(decision) for decision in decisions],
    }
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved gate report to {output_path}")


if __name__ == "__main__":
    main()
