from __future__ import annotations

import math
from pathlib import Path

import torch
from torch.nn import functional as F

from common.io import write_json
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.model import GPTConfig, MiniGPT
from stage2_sft.dataset import extend_tokenizer

IGNORE_INDEX = -100


def load_checkpoint(path: str | Path, device: str) -> tuple[dict, CharTokenizer]:
    checkpoint = torch.load(path, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    return checkpoint, tokenizer


def build_model_config(
    checkpoint: dict,
    tokenizer: CharTokenizer,
    block_size: int,
    dropout: float | None,
) -> GPTConfig:
    base_config = checkpoint["model_config"]
    return GPTConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=max(block_size, base_config["block_size"]),
        n_embed=base_config["n_embed"],
        n_head=base_config["n_head"],
        n_layer=base_config["n_layer"],
        dropout=base_config["dropout"] if dropout is None else dropout,
    )


def initialize_from_checkpoint(model: MiniGPT, checkpoint: dict) -> None:
    source_state = checkpoint["model_state"]
    target_state = model.state_dict()

    for key, source_value in source_state.items():
        if key not in target_state:
            continue
        target_value = target_state[key]
        if source_value.shape == target_value.shape:
            target_state[key] = source_value
            continue
        if key in {"token_embedding.weight", "lm_head.weight"} and source_value.ndim == 2:
            target_value.zero_()
            rows = min(source_value.shape[0], target_value.shape[0])
            cols = min(source_value.shape[1], target_value.shape[1])
            target_value[:rows, :cols] = source_value[:rows, :cols]
            continue
        if key == "lm_head.bias" and source_value.ndim == 1:
            target_value.zero_()
            rows = min(source_value.shape[0], target_value.shape[0])
            target_value[:rows] = source_value[:rows]
            continue
        if key == "position_embedding.weight" and source_value.ndim == 2:
            target_value.zero_()
            rows = min(source_value.shape[0], target_value.shape[0])
            cols = min(source_value.shape[1], target_value.shape[1])
            target_value[:rows, :cols] = source_value[:rows, :cols]
            continue
        if key.endswith(".attn.mask") and source_value.ndim == 2:
            rows = min(source_value.shape[0], target_value.shape[0])
            cols = min(source_value.shape[1], target_value.shape[1])
            target_value[:rows, :cols] = source_value[:rows, :cols]
    model.load_state_dict(target_state)


def prepare_tokenizer(
    base_tokenizer: CharTokenizer,
    training_text: str,
) -> tuple[CharTokenizer, list[str]]:
    return extend_tokenizer(base_tokenizer, training_text)


def sequence_log_probs(model: MiniGPT, input_ids: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    logits, _, _ = model(input_ids)
    log_probs = F.log_softmax(logits, dim=-1)
    gather_labels = labels.masked_fill(labels == IGNORE_INDEX, 0)
    token_log_probs = log_probs.gather(dim=-1, index=gather_labels.unsqueeze(-1)).squeeze(-1)
    token_log_probs = token_log_probs.masked_fill(labels == IGNORE_INDEX, 0.0)
    token_counts = (labels != IGNORE_INDEX).sum(dim=-1).clamp(min=1)
    return token_log_probs.sum(dim=-1) / token_counts


@torch.no_grad()
def evaluate_preference_pairs(
    policy_model: MiniGPT,
    reference_model: MiniGPT,
    pairs: list,
    device: str,
    beta: float,
) -> dict:
    chosen_inputs = torch.stack([pair.chosen_input_ids for pair in pairs]).to(device)
    chosen_labels = torch.stack([pair.chosen_labels for pair in pairs]).to(device)
    rejected_inputs = torch.stack([pair.rejected_input_ids for pair in pairs]).to(device)
    rejected_labels = torch.stack([pair.rejected_labels for pair in pairs]).to(device)

    policy_chosen = sequence_log_probs(policy_model, chosen_inputs, chosen_labels)
    policy_rejected = sequence_log_probs(policy_model, rejected_inputs, rejected_labels)
    ref_chosen = sequence_log_probs(reference_model, chosen_inputs, chosen_labels)
    ref_rejected = sequence_log_probs(reference_model, rejected_inputs, rejected_labels)

    policy_margin = policy_chosen - policy_rejected
    ref_margin = ref_chosen - ref_rejected
    preference_margin = policy_margin - ref_margin
    dpo_loss = -F.logsigmoid(beta * preference_margin).mean().item()
    reference_chosen_win_rate = (ref_margin > 0).float().mean().item()
    policy_chosen_win_rate = (policy_margin > 0).float().mean().item()
    mean_kl_proxy = (
        ((policy_chosen - ref_chosen) ** 2 + (policy_rejected - ref_rejected) ** 2) / 2
    ).mean().item()

    return {
        "pair_count": len(pairs),
        "mean_policy_chosen_logp": policy_chosen.mean().item(),
        "mean_policy_rejected_logp": policy_rejected.mean().item(),
        "mean_policy_margin": policy_margin.mean().item(),
        "mean_reference_margin": ref_margin.mean().item(),
        "mean_preference_margin": preference_margin.mean().item(),
        "policy_chosen_win_rate": policy_chosen_win_rate,
        "reference_chosen_win_rate": reference_chosen_win_rate,
        "chosen_win_rate_delta": policy_chosen_win_rate - reference_chosen_win_rate,
        "mean_kl_proxy": mean_kl_proxy,
        "dpo_loss": dpo_loss,
    }


def format_metrics(metrics: dict) -> str:
    parts = []
    for key, value in metrics.items():
        if isinstance(value, float):
            if math.isfinite(value):
                parts.append(f"{key}={value:.4f}")
            else:
                parts.append(f"{key}={value}")
        else:
            parts.append(f"{key}={value}")
    return " ".join(parts)


def save_training_outputs(
    *,
    out_dir: Path,
    checkpoint_path: Path,
    tokenizer_path: Path,
    training_config: dict,
    model_config: dict,
    added_chars: list[str],
    metrics: dict,
    method: str,
) -> None:
    write_json(
        out_dir / "train_state.json",
        {
            "method": method,
            "checkpoint": str(checkpoint_path),
            "tokenizer": str(tokenizer_path),
            "training_config": training_config,
            "model_config": model_config,
            "added_chars": added_chars,
            "final_metrics": metrics,
        },
    )
