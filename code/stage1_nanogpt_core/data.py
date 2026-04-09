from __future__ import annotations

from pathlib import Path

import torch

from common.tokenizer import CharTokenizer


def load_char_dataset(data_path: str) -> tuple[str, CharTokenizer, torch.Tensor]:
    text = Path(data_path).read_text(encoding="utf-8")
    tokenizer = CharTokenizer.build(text)
    tokens = torch.tensor(tokenizer.encode(text), dtype=torch.long)
    return text, tokenizer, tokens


def split_train_val(tokens: torch.Tensor, train_ratio: float = 0.9) -> tuple[torch.Tensor, torch.Tensor]:
    split_at = int(len(tokens) * train_ratio)
    return tokens[:split_at], tokens[split_at:]


def get_batch(data: torch.Tensor, batch_size: int, block_size: int, device: str) -> tuple[torch.Tensor, torch.Tensor]:
    max_start = len(data) - block_size - 1
    starts = torch.randint(0, max_start, (batch_size,))
    x = torch.stack([data[start : start + block_size] for start in starts])
    y = torch.stack([data[start + 1 : start + block_size + 1] for start in starts])
    return x.to(device), y.to(device)


def decode_window(tokenizer: CharTokenizer, tokens: torch.Tensor) -> list[str]:
    return [tokenizer.decode([int(token_id)]) for token_id in tokens.tolist()]
