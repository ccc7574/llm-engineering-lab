from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--manifest", default="manifests/regression_v2_suite.json")
    parser.add_argument("--policy-path", default="manifests/artifact_lifecycle_policy.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_text(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_output_index(manifest: dict) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for step in manifest.get("steps", []):
        for output_path in step.get("expected_outputs", []):
            index.setdefault(output_path, []).append(step["name"])
    return index


def classify_path(relative_path: str, policy: dict) -> tuple[str, str]:
    for rule in policy.get("rules", []):
        if fnmatch.fnmatch(relative_path, rule["pattern"]):
            return rule["category"], rule["lifecycle"]
    default_rule = policy.get("default", {})
    return default_rule.get("category", "auxiliary"), default_rule.get("lifecycle", "ephemeral_debug")


def markdown_table(rows: list[dict], lifecycle_counts: dict[str, int]) -> str:
    lines = [
        "# Artifact Catalog",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat()}",
        f"- Total artifacts: {len(rows)}",
        f"- Lifecycle counts: {', '.join(f'{key}={value}' for key, value in sorted(lifecycle_counts.items())) or '-'}",
        "",
        "| Path | Category | Lifecycle | Size | Produced By |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        produced_by = ", ".join(row["produced_by_steps"]) or "-"
        lines.append(
            f"| {row['path']} | {row['category']} | {row['lifecycle']} | "
            f"{row['size_bytes']} | {produced_by} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    runs_dir = Path(args.runs_dir)
    manifest = load_json(args.manifest)
    policy = load_json(args.policy_path)
    output_index = build_output_index(manifest)

    rows = []
    lifecycle_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()

    for path in sorted(candidate for candidate in runs_dir.rglob("*") if candidate.is_file()):
        relative_to_runs = path.relative_to(runs_dir)
        display_path = str(Path(runs_dir.name) / relative_to_runs)
        category, lifecycle = classify_path(display_path, policy)
        lifecycle_counter[lifecycle] += 1
        category_counter[category] += 1
        rows.append(
            {
                "path": display_path,
                "source_path": str(path.resolve()),
                "category": category,
                "lifecycle": lifecycle,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_text(path),
                "produced_by_steps": sorted(output_index.get(display_path, [])),
            }
        )

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "runs_dir": str(runs_dir),
        "manifest": str(args.manifest),
        "policy_path": str(args.policy_path),
        "total_artifacts": len(rows),
        "lifecycle_counts": dict(sorted(lifecycle_counter.items())),
        "category_counts": dict(sorted(category_counter.items())),
        "rows": rows,
    }

    print("path\tcategory\tlifecycle\tsize_bytes\tproduced_by")
    for row in rows:
        print(
            f"{row['path']}\t{row['category']}\t{row['lifecycle']}\t"
            f"{row['size_bytes']}\t{','.join(row['produced_by_steps']) or '-'}"
        )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved artifact catalog to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(markdown_table(rows, payload["lifecycle_counts"]), encoding="utf-8")
        print(f"saved artifact catalog markdown to {md_output_path}")


if __name__ == "__main__":
    main()
