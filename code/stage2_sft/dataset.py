from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch

from common.io import load_jsonl
from common.tokenizer import CharTokenizer
from stage2_sft.prompt_template import SFTExample, render_prompt, render_training_text

IGNORE_INDEX = -100
REASONING_INSTRUCTION = (
    "Solve the question step by step. Keep the explanation short and end with a line "
    "that starts with Final Answer:"
)


@dataclass
class EncodedWindow:
    input_ids: torch.Tensor
    labels: torch.Tensor


def _reasoning_output(row: dict) -> str:
    answer = str(row["answer"]).strip()
    rationale = str(row.get("rationale", "")).strip()
    if rationale:
        return f"Reasoning: {rationale}\nFinal Answer: {answer}"
    return f"Final Answer: {answer}"


def row_to_sft_example(row: dict) -> SFTExample:
    if {"instruction", "output"}.issubset(row):
        return SFTExample(
            instruction=row["instruction"],
            input=row.get("input", ""),
            output=row["output"],
        )
    if {"question", "answer"}.issubset(row):
        return SFTExample(
            instruction=REASONING_INSTRUCTION,
            input=row["question"],
            output=_reasoning_output(row),
        )
    raise ValueError(f"unsupported training row keys: {sorted(row.keys())}")


def load_sft_examples(paths: str | Path | list[str] | list[Path]) -> list[SFTExample]:
    if isinstance(paths, (str, Path)):
        path_list = [paths]
    else:
        path_list = list(paths)

    examples = []
    for path in path_list:
        rows = load_jsonl(path)
        examples.extend(row_to_sft_example(row) for row in rows)
    return examples


def collect_training_text(examples: list[SFTExample]) -> str:
    parts = []
    for example in examples:
        prompt, full_text = render_training_text(example)
        parts.append(prompt)
        parts.append(full_text)
    return "\n".join(parts)


def extend_tokenizer(base_tokenizer: CharTokenizer, text: str) -> tuple[CharTokenizer, list[str]]:
    stoi = dict(base_tokenizer.stoi)
    next_index = len(stoi)
    added_chars = []
    for ch in sorted(set(text)):
        if ch in stoi:
            continue
        stoi[ch] = next_index
        next_index += 1
        added_chars.append(ch)
    itos = {idx: ch for ch, idx in stoi.items()}
    return CharTokenizer(stoi=stoi, itos=itos), added_chars


def recommended_block_size(
    examples: list[SFTExample],
    tokenizer: CharTokenizer,
) -> int:
    required = 1
    for example in examples:
        prompt_text, full_text = render_training_text(example)
        prompt_len = len(tokenizer.encode(prompt_text))
        full_len = len(tokenizer.encode(full_text))
        required = max(required, prompt_len, max(full_len - 1, 1))
    return required


def encode_example(example: SFTExample, tokenizer: CharTokenizer) -> tuple[torch.Tensor, torch.Tensor]:
    prompt_text, full_text = render_training_text(example)
    prompt_ids = tokenizer.encode(prompt_text)
    full_ids = tokenizer.encode(full_text)
    if len(full_ids) < 2:
        raise ValueError("example is too short after tokenization")

    input_ids = torch.tensor(full_ids[:-1], dtype=torch.long)
    labels = torch.tensor(full_ids[1:], dtype=torch.long)

    supervised_prefix = max(len(prompt_ids) - 1, 0)
    if supervised_prefix > 0:
        labels[:supervised_prefix] = IGNORE_INDEX
    if torch.all(labels == IGNORE_INDEX):
        raise ValueError("example has no assistant tokens to supervise")
    return input_ids, labels


def make_windows(
    input_ids: torch.Tensor,
    labels: torch.Tensor,
    block_size: int,
) -> list[EncodedWindow]:
    windows = []
    for start in range(0, len(input_ids), block_size):
        chunk_inputs = input_ids[start : start + block_size]
        chunk_labels = labels[start : start + block_size]
        if chunk_inputs.numel() == 0 or torch.all(chunk_labels == IGNORE_INDEX):
            continue
        if chunk_inputs.numel() < block_size:
            pad_len = block_size - chunk_inputs.numel()
            chunk_inputs = torch.cat(
                [chunk_inputs, torch.zeros(pad_len, dtype=torch.long)],
                dim=0,
            )
            chunk_labels = torch.cat(
                [chunk_labels, torch.full((pad_len,), IGNORE_INDEX, dtype=torch.long)],
                dim=0,
            )
        windows.append(EncodedWindow(input_ids=chunk_inputs, labels=chunk_labels))
    if not windows:
        raise ValueError("no trainable windows were created")
    return windows


def build_windows(
    examples: list[SFTExample],
    tokenizer: CharTokenizer,
    block_size: int,
) -> list[EncodedWindow]:
    windows = []
    for example in examples:
        input_ids, labels = encode_example(example, tokenizer)
        windows.extend(make_windows(input_ids, labels, block_size))
    return windows


def sample_batch(
    windows: list[EncodedWindow],
    batch_size: int,
    device: str,
) -> tuple[torch.Tensor, torch.Tensor]:
    indices = torch.randint(0, len(windows), (batch_size,))
    batch_x = torch.stack([windows[idx].input_ids for idx in indices.tolist()]).to(device)
    batch_y = torch.stack([windows[idx].labels for idx in indices.tolist()]).to(device)
    return batch_x, batch_y


def render_eval_prompt(example: SFTExample) -> str:
    return render_prompt(example)
