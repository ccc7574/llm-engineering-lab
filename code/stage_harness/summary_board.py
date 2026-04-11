from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


TRACK_CONFIG = {
    "agentic": {
        "label": "Agentic",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_tool_calls", "avg_steps", "avg_state_reads", "avg_state_writes", "avg_recovery_attempts"],
    },
    "agentic_memory": {
        "label": "Agentic Memory",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_tool_calls", "avg_steps", "avg_state_reads", "avg_state_writes", "avg_recovery_attempts"],
    },
    "agentic_reflection": {
        "label": "Agentic Reflection",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_tool_calls", "avg_steps", "avg_state_reads", "avg_state_writes", "avg_reflection_steps"],
    },
    "agentic_planner": {
        "label": "Agentic Planner/Observer",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": [
            "avg_tool_calls",
            "avg_steps",
            "avg_state_reads",
            "avg_state_writes",
            "avg_planning_steps",
            "avg_observer_checks",
        ],
    },
    "bugfix": {
        "label": "Coding Bugfix",
        "primary_metric": "pass_at_1",
        "quality_gate": 0.05,
        "cost_metrics": [],
    },
    "bugfix_judge": {
        "label": "Coding Judge",
        "primary_metric": "pass_at_1",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_candidates_scored", "avg_total_score"],
    },
    "coding": {
        "label": "Coding Completion",
        "primary_metric": "pass_at_1",
        "quality_gate": 0.05,
        "cost_metrics": [],
    },
    "coding_passk": {
        "label": "Coding Pass@K",
        "primary_metric": "pass_at_k",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_candidates_sampled", "avg_execution_checks", "avg_first_pass_index"],
    },
    "swebench": {
        "label": "Coding SWE-bench Lite",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_repo_reads", "avg_test_runs", "avg_patch_attempts", "avg_triage_reads"],
    },
    "multifile_bugfix": {
        "label": "Coding Multi-File Patch",
        "primary_metric": "pass_at_1",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_touched_files_count", "avg_patch_recall"],
    },
    "agentic_coding": {
        "label": "Coding Agentic Repair",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": [
            "avg_repo_reads",
            "avg_test_runs",
            "avg_patch_attempts",
            "avg_repair_attempts",
            "avg_relevant_context_recall",
            "avg_patch_recall",
        ],
    },
    "multimodal": {
        "label": "Multimodal",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_visual_tokens_used"],
    },
    "multimodal_noisy": {
        "label": "Multimodal Noisy OCR",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_visual_tokens_used", "avg_observation_steps", "avg_reasoning_steps"],
    },
    "multimodal_grounding": {
        "label": "Multimodal Grounding",
        "primary_metric": "task_success_rate",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_visual_tokens_used", "avg_observation_steps", "avg_reasoning_steps"],
    },
    "repo_context": {
        "label": "Coding Repo Context",
        "primary_metric": "pass_at_1",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_selected_context_count", "avg_relevant_context_recall", "avg_context_char_count"],
    },
    "testgen": {
        "label": "Coding Test Generation",
        "primary_metric": "bug_detection_rate",
        "quality_gate": 0.05,
        "cost_metrics": ["avg_generated_tests_count"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--output", default=None)
    parser.add_argument("--registry-path", default=None)
    parser.add_argument("--md-output", default=None)
    return parser.parse_args()


def diff_stem(path: Path) -> str:
    return path.name.removesuffix("_regression_diff.json")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def choose_primary_metric(track_key: str, deltas: dict[str, float]) -> str:
    config = TRACK_CONFIG.get(track_key, {})
    preferred = config.get("primary_metric")
    if preferred in deltas:
        return preferred
    for candidate in ["pass_at_1", "task_success_rate"]:
        if candidate in deltas:
            return candidate
    return next(iter(sorted(deltas)), "delta")


def build_cost_signals(track_key: str, deltas: dict[str, float]) -> list[dict[str, float]]:
    config = TRACK_CONFIG.get(track_key, {})
    metrics = config.get("cost_metrics", [])
    return [{"metric": metric, "delta": float(deltas[metric])} for metric in metrics if metric in deltas]


def quality_status(delta: float, gate: float) -> str:
    if delta < 0:
        return "regressed"
    if delta >= gate:
        return "passed"
    return "flat"


def recommendation(status: str) -> str:
    if status == "passed":
        return "promote candidate and keep monitoring cost signals"
    if status == "flat":
        return "hold change and inspect whether the added complexity is justified"
    return "block rollout and debug the regression before merging"


def format_md_table(rows: list[dict], registry: dict | None) -> str:
    lines = [
        "# Summary Board",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat()}",
        f"- Regression rows: {len(rows)}",
    ]
    if registry:
        lines.append(f"- Registered runs: {registry.get('total_runs', 0)}")
    lines.extend(
        [
            "",
            "| Track | Baseline | Candidate | Delta | Gate | Status | Cost Signals |",
            "| --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in rows:
        cost_signals = ", ".join(
            f"{item['metric']}={item['delta']:+.3f}" for item in row["cost_signals"]
        ) or "-"
        lines.append(
            "| "
            f"{row['label']} | "
            f"{row['baseline_primary']:.3f} | "
            f"{row['candidate_primary']:.3f} | "
            f"{row['quality_delta']:+.3f} | "
            f"{row['quality_gate']:.3f} | "
            f"{row['status']} | "
            f"{cost_signals} |"
        )
    lines.extend(["", "## Recommendations", ""])
    for row in rows:
        lines.append(f"- `{row['label']}`: {row['recommendation']}.")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    runs_dir = Path(args.runs_dir)
    registry = load_json(Path(args.registry_path)) if args.registry_path else None
    rows = []
    for path in sorted(runs_dir.glob("*_regression_diff.json")):
        payload = load_json(path)
        deltas = payload.get("deltas", {})
        track_key = diff_stem(path)
        config = TRACK_CONFIG.get(track_key, {})
        primary_metric = choose_primary_metric(track_key, deltas)
        baseline_report = load_json(Path(payload["baseline_report"]))
        candidate_report = load_json(Path(payload["candidate_report"]))
        baseline_primary = float(baseline_report.get(primary_metric, 0.0))
        candidate_primary = float(candidate_report.get(primary_metric, 0.0))
        quality_delta = float(deltas.get(primary_metric, candidate_primary - baseline_primary))
        gate = float(config.get("quality_gate", 0.0))
        status = quality_status(quality_delta, gate)
        rows.append(
            {
                "track_key": track_key,
                "label": config.get("label", track_key.replace("_", " ")),
                "filename": path.name,
                "primary_metric": primary_metric,
                "baseline_primary": baseline_primary,
                "candidate_primary": candidate_primary,
                "quality_delta": quality_delta,
                "quality_gate": gate,
                "status": status,
                "recommendation": recommendation(status),
                "cost_signals": build_cost_signals(track_key, deltas),
                "baseline_report": payload["baseline_report"],
                "candidate_report": payload["candidate_report"],
                "deltas": deltas,
            }
        )

    print("track\tprimary_metric\tbaseline\tcandidate\tdelta\tstatus")
    for row in rows:
        print(
            f"{row['label']}\t{row['primary_metric']}\t"
            f"{row['baseline_primary']:.3f}\t{row['candidate_primary']:.3f}\t"
            f"{row['quality_delta']:+.3f}\t{row['status']}"
        )

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "runs_dir": str(runs_dir),
        "registry_summary": {
            "path": args.registry_path,
            "total_runs": registry.get("total_runs", 0) if registry else None,
        },
        "rows": rows,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved summary board to {output_path}")
    if args.md_output:
        md_output_path = Path(args.md_output)
        md_output_path.parent.mkdir(parents=True, exist_ok=True)
        md_output_path.write_text(format_md_table(rows, registry), encoding="utf-8")
        print(f"saved markdown summary board to {md_output_path}")


if __name__ == "__main__":
    main()
