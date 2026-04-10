from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path


DEFAULT_LIFECYCLES = ["promote_on_ship", "retain_for_replay"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="runs/artifact_catalog.json")
    parser.add_argument("--label", required=True)
    parser.add_argument("--output-root", default="artifacts/baselines")
    parser.add_argument("--include-lifecycle", action="append", default=[])
    return parser.parse_args()


def load_catalog(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_text(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def markdown_summary(label: str, rows: list[dict], lifecycles: list[str]) -> str:
    lines = [
        f"# Baseline Snapshot `{label}`",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat()}",
        f"- Included lifecycles: {', '.join(lifecycles)}",
        f"- Files copied: {len(rows)}",
        "",
        "| Source | Snapshot | Lifecycle | Verified |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['source_path']} | {row['snapshot_path']} | {row['lifecycle']} | "
            f"{str(row['hash_verified']).lower()} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    catalog = load_catalog(args.catalog)
    lifecycles = args.include_lifecycle or list(DEFAULT_LIFECYCLES)
    output_root = Path(args.output_root)
    snapshot_root = output_root / args.label
    snapshot_root.mkdir(parents=True, exist_ok=True)

    copied_rows = []
    for row in catalog.get("rows", []):
        if row["lifecycle"] not in lifecycles:
            continue
        source_path = Path(row["source_path"])
        relative_path = Path(row["path"])
        target_path = snapshot_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        target_hash = sha256_text(target_path)
        copied_rows.append(
            {
                "path": row["path"],
                "source_path": row["source_path"],
                "snapshot_path": str(target_path),
                "category": row["category"],
                "lifecycle": row["lifecycle"],
                "sha256": row["sha256"],
                "copied_sha256": target_hash,
                "hash_verified": target_hash == row["sha256"],
            }
        )

    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "label": args.label,
        "source_catalog": str(args.catalog),
        "output_root": str(output_root),
        "snapshot_root": str(snapshot_root),
        "included_lifecycles": lifecycles,
        "files_copied": len(copied_rows),
        "rows": copied_rows,
    }
    manifest_path = snapshot_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    readme_path = snapshot_root / "README.md"
    readme_path.write_text(markdown_summary(args.label, copied_rows, lifecycles), encoding="utf-8")

    print(f"label={args.label}")
    print(f"files_copied={len(copied_rows)}")
    print(f"snapshot_root={snapshot_root}")
    print(f"saved manifest to {manifest_path}")
    print(f"saved snapshot readme to {readme_path}")


if __name__ == "__main__":
    main()
