from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch

from common.io import load_jsonl
from common.tokenizer import CharTokenizer

IGNORE_INDEX = -100


@dataclass
class PreferenceExample:
    prompt: str
    chosen: str
    rejected: str


@dataclass
class EncodedPreferencePair:
    chosen_input_ids: torch.Tensor
    chosen_labels: torch.Tensor
    rejected_input_ids: torch.Tensor
    rejected_labels: torch.Tensor


def load_preference_examples(path: str | Path) -> list[PreferenceExample]:
    rows = load_jsonl(path)
    return [
        PreferenceExample(
            prompt=str(row["prompt"]),
            chosen=str(row["chosen"]),
            rejected=str(row["rejected"]),
        )
        for row in rows
    ]


def collect_training_text(examples: list[PreferenceExample]) -> str:
    parts = []
    for example in examples:
        parts.extend([example.prompt, example.chosen, example.rejected])
    return "\n".join(parts)


def recommended_block_size(examples: list[PreferenceExample], tokenizer: CharTokenizer) -> int:
    required = 1
    for example in examples:
        required = max(
            required,
            len(tokenizer.encode(example.prompt + example.chosen)) - 1,
            len(tokenizer.encode(example.prompt + example.rejected)) - 1,
        )
    return max(required, 1)


def encode_completion(
    prompt: str,
    completion: str,
    tokenizer: CharTokenizer,
    block_size: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    prompt_ids = tokenizer.encode(prompt)
    full_ids = tokenizer.encode(prompt + completion)
    if len(full_ids) < 2:
        raise ValueError("preference example is too short after tokenization")

    input_ids = torch.tensor(full_ids[:-1], dtype=torch.long)
    labels = torch.tensor(full_ids[1:], dtype=torch.long)
    supervised_prefix = max(len(prompt_ids) - 1, 0)
    if supervised_prefix > 0:
        labels[:supervised_prefix] = IGNORE_INDEX
    if input_ids.numel() > block_size:
        raise ValueError("preference example exceeds configured block size")
    if input_ids.numel() < block_size:
        pad_len = block_size - input_ids.numel()
        input_ids = torch.cat([input_ids, torch.zeros(pad_len, dtype=torch.long)], dim=0)
        labels = torch.cat([labels, torch.full((pad_len,), IGNORE_INDEX, dtype=torch.long)], dim=0)
    return input_ids, labels


def build_preference_pairs(
    examples: list[PreferenceExample],
    tokenizer: CharTokenizer,
    block_size: int,
) -> list[EncodedPreferencePair]:
    pairs = []
    for example in examples:
        chosen_input_ids, chosen_labels = encode_completion(example.prompt, example.chosen, tokenizer, block_size)
        rejected_input_ids, rejected_labels = encode_completion(example.prompt, example.rejected, tokenizer, block_size)
        pairs.append(
            EncodedPreferencePair(
                chosen_input_ids=chosen_input_ids,
                chosen_labels=chosen_labels,
                rejected_input_ids=rejected_input_ids,
                rejected_labels=rejected_labels,
            )
        )
    if not pairs:
        raise ValueError("no preference pairs were created")
    return pairs


def sample_pair_batch(
    pairs: list[EncodedPreferencePair],
    batch_size: int,
    device: str,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    indices = torch.randint(0, len(pairs), (batch_size,))
    chosen_inputs = torch.stack([pairs[idx].chosen_input_ids for idx in indices.tolist()]).to(device)
    chosen_labels = torch.stack([pairs[idx].chosen_labels for idx in indices.tolist()]).to(device)
    rejected_inputs = torch.stack([pairs[idx].rejected_input_ids for idx in indices.tolist()]).to(device)
    rejected_labels = torch.stack([pairs[idx].rejected_labels for idx in indices.tolist()]).to(device)
    return chosen_inputs, chosen_labels, rejected_inputs, rejected_labels
