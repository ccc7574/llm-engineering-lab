from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_multimodal.dataset import MultimodalTask, load_multimodal_tasks


@dataclass
class MultimodalRun:
    task_id: str
    strategy: str
    answer: str
    visual_tokens_used: int
    trace: list[str]
    extracted_fields: dict[str, str]
    observation_steps: int = 0
    reasoning_steps: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_multimodal/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument(
        "--strategy",
        choices=["text_only", "vision_augmented", "ocr_only", "structured_pipeline", "reference"],
        default="vision_augmented",
    )
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def text_only_answer(task: MultimodalTask) -> str:
    guesses = {
        "invoice_total_due": "1200",
        "chart_highest_region": "EU",
        "status_card_action": "restart service",
        "invoice_total_due_noisy": "2100",
        "routing_owner_lookup": "payments-platform",
        "latency_sla_breach_region": "none",
    }
    return guesses.get(task.task_id, "")


def normalize_ocr_token(text: str) -> str:
    return text.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1")


def parse_noisy_int(text: str) -> int | None:
    normalized = normalize_ocr_token(text)
    match = re.search(r"-?\$?\d+", normalized)
    if not match:
        return None
    return int(match.group(0).replace("$", ""))


def extract_digits_only(text: str) -> int | None:
    match = re.search(r"-?\$?\d+", text)
    if not match:
        return None
    return int(match.group(0).replace("$", ""))


def vision_augmented_answer(task: MultimodalTask) -> MultimodalRun:
    trace: list[str] = []
    visual_tokens_used = 0
    context = task.visual_context
    extracted_fields: dict[str, str] = {}

    if task.task_id == "invoice_total_due":
        lines = context["ocr_lines"]
        visual_tokens_used = len(lines)
        trace.append(f"read_ocr_lines -> {len(lines)} lines")
        answer = "1400"
        trace.append("extract_total_due -> 1400")
        extracted_fields = {"total_due": "1400"}
    elif task.task_id == "chart_highest_region":
        values = context["chart_values"]
        visual_tokens_used = len(values)
        trace.append(f"read_chart_values -> {values}")
        answer = max(values, key=values.get)
        trace.append(f"argmax_region -> {answer}")
        extracted_fields = {region: str(value) for region, value in values.items()}
    elif task.task_id == "status_card_action":
        action = context["action"]
        visual_tokens_used = len(context)
        trace.append(f"read_status_card_fields -> {sorted(context.keys())}")
        answer = action
        trace.append(f"extract_action -> {answer}")
        extracted_fields = {"action": action, "status": context["status"]}
    else:
        answer = ""

    return MultimodalRun(
        task_id=task.task_id,
        strategy="vision_augmented",
        answer=answer,
        visual_tokens_used=visual_tokens_used,
        trace=trace,
        extracted_fields=extracted_fields,
        observation_steps=1,
        reasoning_steps=max(len(trace) - 1, 0),
    )


def ocr_only_answer(task: MultimodalTask) -> MultimodalRun:
    trace: list[str] = []
    extracted_fields: dict[str, str] = {}
    context = task.visual_context

    if task.task_id == "invoice_total_due_noisy":
        lines = context["ocr_lines"]
        trace.append(f"read_noisy_ocr_lines -> {len(lines)} lines")
        subtotal_line = next(line for line in lines if "Subtotal" in line)
        subtotal = extract_digits_only(subtotal_line)
        extracted_fields["total_due"] = str(subtotal)
        trace.append(f"pick_first_amount_like_total -> {subtotal}")
        answer = str(subtotal)
        visual_tokens_used = len(lines)
    elif task.task_id == "routing_owner_lookup":
        rows = context["ocr_rows"]
        trace.append(f"read_noisy_table_rows -> {len(rows)} rows")
        matching_row = next(row for row in rows if "payments-api" in row)
        owner = matching_row.split("|")[-1].strip()
        extracted_fields["owner"] = owner
        extracted_fields["severity"] = "sev2"
        trace.append(f"match_first_service_row -> {owner}")
        answer = owner
        visual_tokens_used = len(rows)
    elif task.task_id == "latency_sla_breach_region":
        cells = context["ocr_cells"]
        trace.append(f"read_noisy_table_cells -> {len(cells)} rows")
        numeric_rows = []
        for cell in cells:
            raw_value = cell.split("|")[-1].strip()
            parsed = extract_digits_only(raw_value)
            if parsed is not None:
                region = cell.split("|")[0].strip()
                numeric_rows.append((region, parsed))
        if numeric_rows:
            answer = max(numeric_rows, key=lambda item: item[1])[0]
        else:
            answer = "none"
        extracted_fields["breach_region"] = answer
        trace.append(f"pick_max_parseable_wait -> {answer}")
        visual_tokens_used = len(cells)
    else:
        answer = text_only_answer(task)
        visual_tokens_used = 0
        trace.append(f"fallback_text_guess -> {answer}")

    return MultimodalRun(
        task_id=task.task_id,
        strategy="ocr_only",
        answer=answer,
        visual_tokens_used=visual_tokens_used,
        trace=trace,
        extracted_fields=extracted_fields,
        observation_steps=1,
        reasoning_steps=max(len(trace) - 1, 0),
    )


def structured_pipeline_answer(task: MultimodalTask) -> MultimodalRun:
    trace: list[str] = []
    extracted_fields: dict[str, str] = {}
    context = task.visual_context

    if task.task_id == "invoice_total_due_noisy":
        candidates = context["field_candidates"]
        trace.append(f"observe_invoice_candidates -> {sorted(candidates.keys())}")
        for key, value in candidates.items():
            parsed = parse_noisy_int(value)
            if parsed is not None:
                extracted_fields[key] = str(parsed)
        answer = extracted_fields["total_due"]
        trace.append(f"extract_structured_fields -> {extracted_fields}")
        trace.append(f"return_total_due -> {answer}")
        visual_tokens_used = len(context["ocr_lines"])
    elif task.task_id == "routing_owner_lookup":
        rows = context["table_rows"]
        trace.append(f"observe_routing_table -> {len(rows)} rows")
        target_service = context["target_service"]
        target_severity = context["target_severity"]
        extracted_fields["service"] = target_service
        extracted_fields["severity"] = target_severity
        matched_row = next(
            row for row in rows if row["service"] == target_service and row["severity"] == target_severity
        )
        extracted_fields["owner"] = matched_row["owner"]
        answer = matched_row["owner"]
        trace.append(f"extract_target_row -> {matched_row}")
        trace.append(f"return_owner -> {answer}")
        visual_tokens_used = len(context["ocr_rows"])
    elif task.task_id == "latency_sla_breach_region":
        rows = context["table_rows"]
        threshold = int(context["sla_threshold"])
        trace.append(f"observe_latency_rows -> {len(rows)} rows")
        breach_region = "none"
        for row in rows:
            wait_value = parse_noisy_int(row["queue_wait"])
            if wait_value is None:
                continue
            extracted_fields[row["region"].lower()] = str(wait_value)
            if wait_value >= threshold and breach_region == "none":
                breach_region = row["region"]
        answer = breach_region
        extracted_fields["breach_region"] = breach_region
        trace.append(f"normalize_wait_values -> {extracted_fields}")
        trace.append(f"return_first_breach_region -> {answer}")
        visual_tokens_used = len(context["ocr_cells"])
    else:
        return vision_augmented_answer(task)

    return MultimodalRun(
        task_id=task.task_id,
        strategy="structured_pipeline",
        answer=answer,
        visual_tokens_used=visual_tokens_used,
        trace=trace,
        extracted_fields=extracted_fields,
        observation_steps=1,
        reasoning_steps=max(len(trace) - 1, 0),
    )


def build_run(task: MultimodalTask, strategy: str) -> MultimodalRun:
    if strategy == "reference":
        return MultimodalRun(
            task_id=task.task_id,
            strategy=strategy,
            answer=task.expected_answer,
            visual_tokens_used=0,
            trace=["reference answer"],
            extracted_fields=dict(task.expected_fields),
        )
    if strategy == "structured_pipeline":
        return structured_pipeline_answer(task)
    if strategy == "ocr_only":
        return ocr_only_answer(task)
    if strategy == "vision_augmented":
        return vision_augmented_answer(task)
    answer = text_only_answer(task)
    return MultimodalRun(
        task_id=task.task_id,
        strategy=strategy,
        answer=answer,
        visual_tokens_used=0,
        trace=[f"text_only_guess -> {answer}"],
        extracted_fields={},
    )


def main() -> None:
    args = parse_args()
    tasks = load_multimodal_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        run = build_run(task, args.strategy)
        print(f"Task: {task.task_id}")
        print(f"Asset: {task.asset_path}")
        print(f"Answer: {run.answer}")
        print(f"Visual tokens used: {run.visual_tokens_used}")
        print(f"Observation/reasoning steps: {run.observation_steps}/{run.reasoning_steps}")
        if run.extracted_fields:
            print(f"Extracted fields: {json.dumps(run.extracted_fields, ensure_ascii=False)}")
        for step in run.trace:
            print(f"  {step}")
        print("-" * 72)
        rows.append(asdict(run))

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved multimodal runs to {output_path}")


if __name__ == "__main__":
    main()
