from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CharTokenizer:
    stoi: dict[str, int]
    itos: dict[int, str]

    @classmethod
    def build(cls, text: str) -> "CharTokenizer":
        vocab = sorted(set(text))
        stoi = {ch: idx for idx, ch in enumerate(vocab)}
        itos = {idx: ch for ch, idx in stoi.items()}
        return cls(stoi=stoi, itos=itos)

    @property
    def vocab_size(self) -> int:
        return len(self.stoi)

    def encode(self, text: str) -> list[int]:
        unknown = [ch for ch in text if ch not in self.stoi]
        if unknown:
            missing = "".join(sorted(set(unknown[:5])))
            raise ValueError(f"text contains characters outside tokenizer vocab: {missing!r}")
        return [self.stoi[ch] for ch in text]

    def decode(self, token_ids: list[int]) -> str:
        return "".join(self.itos[idx] for idx in token_ids)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "stoi": self.stoi,
            "itos": {str(idx): ch for idx, ch in self.itos.items()},
        }
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "CharTokenizer":
        with Path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        stoi = {str(ch): int(idx) for ch, idx in payload["stoi"].items()}
        itos = {int(idx): ch for idx, ch in payload["itos"].items()}
        return cls(stoi=stoi, itos=itos)
