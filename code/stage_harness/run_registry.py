from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class RunRecord:
    name: str
    path: str
    category: str
    track: str
    checkpoint: str | None
    tokenizer: str | None
    device: str | None
    max_iters: int | None
    block_size: int | None


def infer_category(run_name: str) -> str:
    lowered = run_name.lower()
    if "smoke" in lowered:
        return "smoke"
    if "golden" in lowered or "baseline" in lowered:
        return "baseline"
    return "candidate"


def infer_track(run_name: str) -> str:
    lowered = run_name.lower()
    if lowered.startswith("stage0") or lowered.startswith("stage1"):
        return "pretraining"
    if lowered.startswith("stage2") or lowered.startswith("stage3") or lowered.startswith("stage4") or lowered.startswith("stage5"):
        return "post_training"
    if "coding" in lowered:
        return "coding"
    return "unknown"


def load_run_record(train_state_path: Path) -> RunRecord:
    import json

    payload = json.loads(train_state_path.read_text(encoding="utf-8"))
    training_config = payload.get("training_config", {})
    model_config = payload.get("model_config", {})
    run_name = train_state_path.parent.name
    return RunRecord(
        name=run_name,
        path=str(train_state_path.parent),
        category=infer_category(run_name),
        track=infer_track(run_name),
        checkpoint=payload.get("checkpoint"),
        tokenizer=payload.get("tokenizer"),
        device=payload.get("device"),
        max_iters=training_config.get("max_iters"),
        block_size=model_config.get("block_size", training_config.get("block_size")),
    )


def scan_runs(runs_dir: str | Path) -> list[RunRecord]:
    root = Path(runs_dir)
    records = []
    for train_state_path in sorted(root.glob("*/train_state.json")):
        records.append(load_run_record(train_state_path))
    return records


def records_as_rows(records: list[RunRecord]) -> list[dict]:
    return [asdict(record) for record in records]
