from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io import load_jsonl
from common.runtime import choose_device
from common.tokenizer import CharTokenizer
from stage4_verifier.features import build_numeric_features
from stage4_verifier.model import MiniVerifier, VerifierConfig
from stage4_verifier.train_verifier import SEPARATOR


@dataclass
class ScoredCandidate:
    candidate: str
    score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="runs/stage4_verifier/ckpt.pt")
    parser.add_argument("--prompt-file", default="datasets/tiny_verifier/demo_candidates.jsonl")
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def load_model(checkpoint_path: str, device: str) -> tuple[MiniVerifier, CharTokenizer]:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    model = MiniVerifier(VerifierConfig(**checkpoint["model_config"])).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, tokenizer


def make_tokenizer_compatible(text: str, tokenizer: CharTokenizer) -> str:
    compatible = []
    for ch in text:
        if ch in tokenizer.stoi:
            compatible.append(ch)
            continue
        lowered = ch.lower()
        if lowered in tokenizer.stoi:
            compatible.append(lowered)
            continue
        uppered = ch.upper()
        if uppered in tokenizer.stoi:
            compatible.append(uppered)
            continue
        compatible.append(" " if " " in tokenizer.stoi else "")
    return "".join(compatible)


@torch.no_grad()
def score_candidate(
    model: MiniVerifier,
    tokenizer: CharTokenizer,
    prompt: str,
    candidate: str,
    device: str,
) -> float:
    rendered = f"{prompt.strip()}{SEPARATOR}{candidate.strip()}"
    token_ids = tokenizer.encode(make_tokenizer_compatible(rendered, tokenizer))
    token_ids = token_ids[-model.config.block_size :]
    input_ids = torch.tensor([token_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids)
    numeric_features = build_numeric_features(prompt, candidate).unsqueeze(0).to(device)
    logits = model(input_ids, attention_mask, numeric_features)
    return torch.sigmoid(logits)[0].item()


def score_candidates(
    model: MiniVerifier,
    tokenizer: CharTokenizer,
    prompt: str,
    candidates: list[str],
    device: str,
) -> list[ScoredCandidate]:
    return [
        ScoredCandidate(
            candidate=candidate,
            score=score_candidate(model, tokenizer, prompt, candidate, device),
        )
        for candidate in candidates
    ]


def rerank_candidates(
    model: MiniVerifier,
    tokenizer: CharTokenizer,
    prompt: str,
    candidates: list[str],
    device: str,
) -> list[ScoredCandidate]:
    scored = score_candidates(model, tokenizer, prompt, candidates, device)
    return sorted(scored, key=lambda item: item.score, reverse=True)


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    model, tokenizer = load_model(args.checkpoint, device)
    rows = load_jsonl(args.prompt_file)

    for index, row in enumerate(rows, start=1):
        prompt = row["prompt"]
        candidates = row["candidates"]
        scored = score_candidates(model, tokenizer, prompt, candidates, device)
        reranked = rerank_candidates(model, tokenizer, prompt, candidates, device)

        print(f"Example {index}")
        print(f"Prompt: {prompt}")
        print("Original order:")
        for position, item in enumerate(scored, start=1):
            print(f"  {position}. score={item.score:.3f} | {item.candidate}")
        print("Reranked:")
        for position, item in enumerate(reranked, start=1):
            print(f"  {position}. score={item.score:.3f} | {item.candidate}")
        print("-" * 72)


if __name__ == "__main__":
    main()
