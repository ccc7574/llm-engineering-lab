from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn

from common.io import load_jsonl
from stage_multimodal.dataset import MultimodalTask, load_multimodal_tasks


ROUTE_LABELS = [
    "vision_augmented",
    "structured_pipeline",
    "grounded_pipeline",
    "document_pipeline",
]


def count_bucket(count: int) -> str:
    if count <= 0:
        return "0"
    if count == 1:
        return "1"
    if count == 2:
        return "2"
    if count <= 4:
        return "3_4"
    return "5_plus"


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def _add_row_shape_features(features: set[str], rows: list[dict], prefix: str) -> None:
    if not rows:
        return
    features.add(f"{prefix}:count_bucket:{count_bucket(len(rows))}")
    for key in sorted(rows[0].keys()):
        features.add(f"{prefix}:column:{key}")


def feature_keys_for_task(task: MultimodalTask) -> list[str]:
    context = task.visual_context
    features: set[str] = {"bias"}

    for token in tokenize(task.instruction):
        features.add(f"instruction:{token}")

    doc_type = str(context.get("doc_type", "")).strip().lower()
    if doc_type:
        features.add(f"doc_type:{doc_type}")

    chart_type = str(context.get("chart_type", "")).strip().lower()
    if chart_type:
        features.add(f"chart_type:{chart_type}")

    for key in sorted(context.keys()):
        features.add(f"context_key:{key}")

    if "ocr_lines" in context:
        features.add("single_page:ocr_lines")
        features.add(f"ocr_lines:count_bucket:{count_bucket(len(context['ocr_lines']))}")
    if "ocr_rows" in context:
        features.add("single_page:ocr_rows")
        features.add(f"ocr_rows:count_bucket:{count_bucket(len(context['ocr_rows']))}")
    if "ocr_cells" in context:
        features.add("single_page:ocr_cells")
        features.add(f"ocr_cells:count_bucket:{count_bucket(len(context['ocr_cells']))}")
    if "field_candidates" in context:
        features.add("single_page:field_candidates")
        features.add(f"field_candidates:count_bucket:{count_bucket(len(context['field_candidates']))}")
    if "table_rows" in context:
        features.add("single_page:table_rows")
        _add_row_shape_features(features, list(context["table_rows"]), "single_page_table")
    if "regions" in context:
        features.add("single_page:regions")
        features.add(f"regions:count_bucket:{count_bucket(len(context['regions']))}")
        for region in context["regions"]:
            label = str(region.get("label", "")).strip().lower()
            region_id = str(region.get("region_id", "")).strip().lower()
            if label:
                features.add(f"region_label:{label}")
            if region_id:
                features.add(f"region_id:{region_id}")

    pages = list(context.get("pages", []))
    if pages:
        features.add("context_key:pages")
        features.add(f"pages:count_bucket:{count_bucket(len(pages))}")
        pages_with_table = 0
        pages_with_fields = 0
        pages_with_regions = 0
        for page in pages:
            role = str(page.get("doc_role", "")).strip().lower()
            if role:
                features.add(f"page_role:{role}")
            if page.get("field_candidates"):
                pages_with_fields += 1
                features.add("page_has:field_candidates")
            if page.get("table_rows"):
                pages_with_table += 1
                features.add("page_has:table_rows")
                _add_row_shape_features(features, list(page["table_rows"]), "page_table")
            if page.get("regions"):
                pages_with_regions += 1
                features.add("page_has:regions")
                for region in page["regions"]:
                    label = str(region.get("label", "")).strip().lower()
                    region_id = str(region.get("region_id", "")).strip().lower()
                    if label:
                        features.add(f"page_region_label:{label}")
                    if region_id:
                        features.add(f"page_region_id:{region_id}")
        features.add(f"pages_with_table:{count_bucket(pages_with_table)}")
        features.add(f"pages_with_fields:{count_bucket(pages_with_fields)}")
        features.add(f"pages_with_regions:{count_bucket(pages_with_regions)}")
        if pages_with_fields and pages_with_table and len(pages) >= 2:
            features.add("workflow:cross_page_field_plus_table")

    hints = dict(context.get("grounding_hints", {}))
    if hints:
        features.add("context_key:grounding_hints")
        for key, value in sorted(hints.items()):
            features.add(f"hint_key:{key}")
            normalized_value = str(value).strip().lower()
            if normalized_value:
                features.add(f"hint_value:{normalized_value}")

    return sorted(features)


def build_feature_vocab(tasks: list[MultimodalTask]) -> list[str]:
    vocab: set[str] = set()
    for task in tasks:
        vocab.update(feature_keys_for_task(task))
    return sorted(vocab)


def label_counts(tasks: list[MultimodalTask]) -> dict[str, int]:
    counts = Counter(task.target_strategy for task in tasks if task.target_strategy)
    return {label: counts.get(label, 0) for label in ROUTE_LABELS}


def vectorize_tasks(tasks: list[MultimodalTask], feature_vocab: list[str]) -> torch.Tensor:
    vocab_index = {feature: idx for idx, feature in enumerate(feature_vocab)}
    matrix = torch.zeros((len(tasks), len(feature_vocab)), dtype=torch.float32)
    for row_idx, task in enumerate(tasks):
        for feature in feature_keys_for_task(task):
            feature_idx = vocab_index.get(feature)
            if feature_idx is not None:
                matrix[row_idx, feature_idx] = 1.0
    return matrix


def label_tensor(tasks: list[MultimodalTask]) -> torch.Tensor:
    label_to_idx = {label: idx for idx, label in enumerate(ROUTE_LABELS)}
    missing = [task.task_id for task in tasks if task.target_strategy not in label_to_idx]
    if missing:
        raise ValueError(f"missing or invalid target_strategy for tasks: {', '.join(missing)}")
    return torch.tensor([label_to_idx[task.target_strategy] for task in tasks], dtype=torch.long)


class LinearRoutePolicy(nn.Module):
    def __init__(self, input_dim: int, output_dim: int) -> None:
        super().__init__()
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.linear(features)


@dataclass
class RoutePrediction:
    strategy: str
    confidence: float
    scores: dict[str, float]


def predict_route(
    model: LinearRoutePolicy,
    feature_vocab: list[str],
    task: MultimodalTask,
    device: str = "cpu",
) -> RoutePrediction:
    model.eval()
    with torch.no_grad():
        features = vectorize_tasks([task], feature_vocab).to(device)
        logits = model(features)[0]
        probs = torch.softmax(logits, dim=0)
        index = int(torch.argmax(probs).item())
    return RoutePrediction(
        strategy=ROUTE_LABELS[index],
        confidence=float(probs[index].item()),
        scores={label: float(probs[idx].item()) for idx, label in enumerate(ROUTE_LABELS)},
    )


def heuristic_route(task: MultimodalTask) -> RoutePrediction:
    context = task.visual_context
    if "pages" in context or "regions" in context:
        strategy = "grounded_pipeline"
    elif any(key in context for key in ["field_candidates", "table_rows", "ocr_rows", "ocr_cells"]):
        strategy = "structured_pipeline"
    else:
        strategy = "vision_augmented"
    return RoutePrediction(
        strategy=strategy,
        confidence=1.0,
        scores={label: 1.0 if label == strategy else 0.0 for label in ROUTE_LABELS},
    )


def load_route_tasks(path: str | Path) -> list[MultimodalTask]:
    return load_multimodal_tasks(path)


def load_route_rows(path: str | Path) -> list[dict]:
    return load_jsonl(path)


def load_route_policy(checkpoint_path: str | Path, device: str = "cpu") -> tuple[LinearRoutePolicy, list[str]]:
    payload = torch.load(checkpoint_path, map_location=device)
    feature_vocab = list(payload["feature_vocab"])
    model = LinearRoutePolicy(len(feature_vocab), len(ROUTE_LABELS)).to(device)
    model.load_state_dict(payload["model_state"])
    model.eval()
    return model, feature_vocab
