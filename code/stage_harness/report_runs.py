from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_harness.run_registry import records_as_rows, scan_runs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = scan_runs(args.runs_dir)

    print("name\tcategory\ttrack\tdevice\tmax_iters\tblock_size")
    for record in records:
        print(
            f"{record.name}\t{record.category}\t{record.track}\t"
            f"{record.device or '-'}\t{record.max_iters or '-'}\t{record.block_size or '-'}"
        )

    payload = {
        "runs_dir": args.runs_dir,
        "total_runs": len(records),
        "records": records_as_rows(records),
    }

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved run registry to {output_path}")


if __name__ == "__main__":
    main()
