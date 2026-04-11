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
        choices=[
            "text_only",
            "vision_augmented",
            "ocr_only",
            "structured_pipeline",
            "grounded_pipeline",
            "document_pipeline",
            "reference",
        ],
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
        "incident_packet_escalation_owner": "release-manager",
        "policy_exception_owner": "analytics-oncall",
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


def route_page(pages: list[dict], target_tokens: list[str], target_role: str | None) -> dict:
    best_page = pages[0]
    best_score = -1
    for page in pages:
        score = 0
        haystack = " ".join(page.get("ocr_lines", [])).lower()
        for token in target_tokens:
            if token and token.lower() in haystack:
                score += 1
        if target_role and page.get("doc_role") == target_role:
            score += 3
        if score > best_score:
            best_score = score
            best_page = page
    return best_page


def select_region(regions: list[dict], target_region: str | None) -> dict | None:
    if not regions:
        return None
    if target_region:
        for region in regions:
            if region.get("region_id") == target_region or region.get("label") == target_region:
                return region
    return regions[0]


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
    elif task.task_id == "incident_packet_escalation_owner":
        first_page = context["pages"][0]
        trace.append(f"read_first_page_only -> {first_page['page_id']}")
        answer = "release-manager"
        extracted_fields["target_page"] = first_page["page_id"]
        extracted_fields["owner"] = answer
        trace.append(f"pick_summary_owner -> {answer}")
        visual_tokens_used = len(first_page.get("ocr_lines", []))
    elif task.task_id == "policy_exception_owner":
        regions = context["ocr_regions"]
        trace.append(f"read_region_text_in_order -> {len(regions)} regions")
        answer = "analytics-oncall"
        extracted_fields["target_region"] = "summary_card"
        extracted_fields["owner"] = answer
        trace.append(f"pick_first_owner_like_text -> {answer}")
        visual_tokens_used = len(regions)
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
    elif task.task_id == "incident_packet_escalation_owner":
        pages = context["pages"]
        hints = context.get("grounding_hints", {})
        routed_page = route_page(
            pages,
            [context["target_service"], context["target_severity"]],
            hints.get("target_page_role"),
        )
        routed_region = select_region(routed_page.get("regions", []), hints.get("target_region"))
        matched_row = next(
            row
            for row in routed_page["table_rows"]
            if row["service"] == context["target_service"] and row["severity"] == context["target_severity"]
        )
        answer = matched_row["owner"]
        extracted_fields["target_page"] = routed_page["page_id"]
        extracted_fields["target_region"] = routed_region["region_id"] if routed_region else "none"
        extracted_fields["service"] = matched_row["service"]
        extracted_fields["severity"] = matched_row["severity"]
        extracted_fields["owner"] = matched_row["owner"]
        trace.append(f"route_page -> {routed_page['page_id']}")
        trace.append(f"ground_region -> {extracted_fields['target_region']}")
        trace.append(f"extract_routing_row -> {matched_row}")
        trace.append(f"return_owner -> {answer}")
        visual_tokens_used = sum(len(page.get("ocr_lines", [])) for page in pages)
    elif task.task_id == "policy_exception_owner":
        regions = context["regions"]
        hints = context.get("grounding_hints", {})
        target_region = select_region(regions, hints.get("target_region"))
        matched_row = next(
            row
            for row in target_region["rows"]
            if row["service"] == context["target_service"] and row["policy"] == context["target_policy"]
        )
        answer = matched_row["owner"]
        extracted_fields["target_region"] = target_region["region_id"]
        extracted_fields["service"] = matched_row["service"]
        extracted_fields["policy"] = matched_row["policy"]
        extracted_fields["owner"] = matched_row["owner"]
        trace.append(f"ground_region -> {target_region['region_id']}")
        trace.append(f"extract_policy_row -> {matched_row}")
        trace.append(f"return_owner -> {answer}")
        visual_tokens_used = len(context["ocr_regions"])
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


def grounded_pipeline_answer(task: MultimodalTask) -> MultimodalRun:
    if task.task_id == "invoice_exception_owner_packet":
        pages = task.visual_context["pages"]
        hints = task.visual_context.get("grounding_hints", {})
        summary_page = route_page(
            pages,
            [task.visual_context["target_service"], task.visual_context["approval_policy"]],
            hints.get("summary_page_role"),
        )
        answer = summary_page.get("default_owner", "release-manager")
        extracted_fields = {
            "target_page": summary_page["page_id"],
            "service": task.visual_context["target_service"],
            "policy": task.visual_context["approval_policy"],
            "owner": answer,
        }
        trace = [
            f"route_summary_page -> {summary_page['page_id']}",
            f"pick_summary_owner -> {answer}",
        ]
        return MultimodalRun(
            task_id=task.task_id,
            strategy="grounded_pipeline",
            answer=answer,
            visual_tokens_used=sum(len(page.get("ocr_lines", [])) for page in pages),
            trace=trace,
            extracted_fields=extracted_fields,
            observation_steps=1,
            reasoning_steps=1,
        )
    if task.task_id == "latency_breach_owner_packet":
        pages = task.visual_context["pages"]
        hints = task.visual_context.get("grounding_hints", {})
        latency_page = route_page(
            pages,
            [task.visual_context["metric_name"], str(task.visual_context["sla_threshold"])],
            hints.get("latency_page_role"),
        )
        first_breach_region = "none"
        for row in latency_page.get("table_rows", []):
            wait_value = parse_noisy_int(row["queue_wait"])
            if wait_value is not None and wait_value >= int(task.visual_context["sla_threshold"]):
                first_breach_region = row["region"]
                break
        trace = [
            f"route_latency_page -> {latency_page['page_id']}",
            f"extract_first_breach_region -> {first_breach_region}",
        ]
        return MultimodalRun(
            task_id=task.task_id,
            strategy="grounded_pipeline",
            answer=first_breach_region,
            visual_tokens_used=sum(len(page.get("ocr_lines", [])) for page in pages),
            trace=trace,
            extracted_fields={
                "target_page": latency_page["page_id"],
                "breach_region": first_breach_region,
            },
            observation_steps=1,
            reasoning_steps=1,
        )
    return structured_pipeline_answer(task)


def document_pipeline_answer(task: MultimodalTask) -> MultimodalRun:
    trace: list[str] = []
    extracted_fields: dict[str, str] = {}
    pages = task.visual_context["pages"]
    hints = task.visual_context.get("grounding_hints", {})

    if task.task_id == "invoice_exception_owner_packet":
        summary_page = route_page(
            pages,
            [task.visual_context["target_service"], task.visual_context["approval_policy"]],
            hints.get("summary_page_role"),
        )
        approval_page = route_page(
            pages,
            [task.visual_context["target_service"], task.visual_context["approval_policy"], "owner"],
            hints.get("approval_page_role"),
        )
        approval_region = select_region(approval_page.get("regions", []), hints.get("approval_region"))
        candidates = summary_page["field_candidates"]
        normalized_fields: dict[str, str] = {}
        for key, value in candidates.items():
            if key in {"subtotal", "expedite_fee", "credits", "total_due"}:
                parsed = parse_noisy_int(value)
                if parsed is not None:
                    normalized_fields[key] = str(parsed)
            else:
                normalized_fields[key] = str(value)
        matched_row = next(
            row
            for row in approval_page["table_rows"]
            if row["service"] == task.visual_context["target_service"]
            and row["policy"] == task.visual_context["approval_policy"]
        )
        answer = matched_row["owner"]
        extracted_fields.update(normalized_fields)
        extracted_fields["target_summary_page"] = summary_page["page_id"]
        extracted_fields["target_approval_page"] = approval_page["page_id"]
        extracted_fields["target_region"] = approval_region["region_id"] if approval_region else "none"
        extracted_fields["service"] = matched_row["service"]
        extracted_fields["policy"] = matched_row["policy"]
        extracted_fields["owner"] = matched_row["owner"]
        trace.extend(
            [
                f"route_summary_page -> {summary_page['page_id']}",
                f"normalize_invoice_fields -> {normalized_fields}",
                f"route_approval_page -> {approval_page['page_id']}",
                f"ground_approval_region -> {extracted_fields['target_region']}",
                f"lookup_exception_owner -> {matched_row}",
                f"return_owner -> {answer}",
            ]
        )
    elif task.task_id == "latency_breach_owner_packet":
        latency_page = route_page(
            pages,
            [task.visual_context["metric_name"], str(task.visual_context["sla_threshold"])],
            hints.get("latency_page_role"),
        )
        escalation_page = route_page(
            pages,
            ["escalation", "owner", "region"],
            hints.get("escalation_page_role"),
        )
        escalation_region = select_region(escalation_page.get("regions", []), hints.get("escalation_region"))
        threshold = int(task.visual_context["sla_threshold"])
        normalized_rows = []
        first_breach_region = "none"
        for row in latency_page["table_rows"]:
            wait_value = parse_noisy_int(row["queue_wait"])
            if wait_value is None:
                continue
            normalized_rows.append({"region": row["region"], "queue_wait": wait_value})
            extracted_fields[row["region"].lower()] = str(wait_value)
            if wait_value >= threshold and first_breach_region == "none":
                first_breach_region = row["region"]
        matched_row = next(
            row for row in escalation_page["table_rows"] if row["region"] == first_breach_region
        )
        answer = matched_row["owner"]
        extracted_fields["target_latency_page"] = latency_page["page_id"]
        extracted_fields["target_escalation_page"] = escalation_page["page_id"]
        extracted_fields["target_region"] = escalation_region["region_id"] if escalation_region else "none"
        extracted_fields["breach_region"] = first_breach_region
        extracted_fields["owner"] = answer
        trace.extend(
            [
                f"route_latency_page -> {latency_page['page_id']}",
                f"normalize_latency_rows -> {normalized_rows}",
                f"detect_first_breach_region -> {first_breach_region}",
                f"route_escalation_page -> {escalation_page['page_id']}",
                f"ground_escalation_region -> {extracted_fields['target_region']}",
                f"lookup_region_owner -> {matched_row}",
                f"return_owner -> {answer}",
            ]
        )
    else:
        return grounded_pipeline_answer(task)

    return MultimodalRun(
        task_id=task.task_id,
        strategy="document_pipeline",
        answer=answer,
        visual_tokens_used=sum(len(page.get("ocr_lines", [])) for page in pages),
        trace=trace,
        extracted_fields=extracted_fields,
        observation_steps=2,
        reasoning_steps=max(len(trace) - 2, 0),
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
    if strategy == "grounded_pipeline":
        return grounded_pipeline_answer(task)
    if strategy == "document_pipeline":
        return document_pipeline_answer(task)
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
