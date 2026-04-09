from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from torch.nn import functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io import load_jsonl, write_json
from common.runtime import choose_device, ensure_dir, set_seed
from common.tokenizer import CharTokenizer
from stage4_verifier.features import build_numeric_features
from stage4_verifier.model import MiniVerifier, VerifierConfig

SEPARATOR = "\nCandidate:\n"


@dataclass
class VerifierExample:
    prompt: str
    candidate: str
    label: int


@dataclass
class EncodedExample:
    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    numeric_features: torch.Tensor
    label: torch.Tensor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_verifier/train.jsonl")
    parser.add_argument("--out-dir", default="runs/stage4_verifier")
    parser.add_argument("--max-iters", type=int, default=300)
    parser.add_argument("--eval-interval", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--block-size", type=int, default=192)
    parser.add_argument("--n-embed", type=int, default=48)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def load_examples(path: str | Path) -> list[VerifierExample]:
    rows = load_jsonl(path)
    return [
        VerifierExample(
            prompt=row["prompt"],
            candidate=row["candidate"],
            label=int(row["label"]),
        )
        for row in rows
    ]


def render_verifier_text(example: VerifierExample) -> str:
    return f"{example.prompt.strip()}{SEPARATOR}{example.candidate.strip()}"


def build_tokenizer(examples: list[VerifierExample]) -> CharTokenizer:
    text = "\n".join(render_verifier_text(example) for example in examples)
    return CharTokenizer.build(text)


def recommended_block_size(
    examples: list[VerifierExample],
    tokenizer: CharTokenizer,
) -> int:
    required = 1
    for example in examples:
        required = max(required, len(tokenizer.encode(render_verifier_text(example))))
    return required


def encode_example(
    example: VerifierExample,
    tokenizer: CharTokenizer,
    block_size: int,
) -> EncodedExample:
    token_ids = tokenizer.encode(render_verifier_text(example))
    token_ids = token_ids[-block_size:]
    attention_mask = torch.ones(len(token_ids), dtype=torch.long)
    input_ids = torch.tensor(token_ids, dtype=torch.long)
    if input_ids.numel() < block_size:
        pad_len = block_size - input_ids.numel()
        input_ids = torch.cat([input_ids, torch.zeros(pad_len, dtype=torch.long)], dim=0)
        attention_mask = torch.cat([attention_mask, torch.zeros(pad_len, dtype=torch.long)], dim=0)
    return EncodedExample(
        input_ids=input_ids,
        attention_mask=attention_mask,
        numeric_features=build_numeric_features(example.prompt, example.candidate),
        label=torch.tensor(float(example.label), dtype=torch.float32),
    )


def build_dataset(
    examples: list[VerifierExample],
    tokenizer: CharTokenizer,
    block_size: int,
) -> list[EncodedExample]:
    return [encode_example(example, tokenizer, block_size) for example in examples]


def sample_batch(
    examples: list[EncodedExample],
    batch_size: int,
    device: str,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    indices = torch.randint(0, len(examples), (batch_size,))
    input_ids = torch.stack([examples[idx].input_ids for idx in indices.tolist()]).to(device)
    attention_mask = torch.stack([examples[idx].attention_mask for idx in indices.tolist()]).to(device)
    numeric_features = torch.stack([examples[idx].numeric_features for idx in indices.tolist()]).to(device)
    labels = torch.stack([examples[idx].label for idx in indices.tolist()]).to(device)
    return input_ids, attention_mask, numeric_features, labels


@torch.no_grad()
def evaluate(model: MiniVerifier, examples: list[EncodedExample], device: str) -> dict[str, float]:
    model.eval()
    input_ids = torch.stack([example.input_ids for example in examples]).to(device)
    attention_mask = torch.stack([example.attention_mask for example in examples]).to(device)
    numeric_features = torch.stack([example.numeric_features for example in examples]).to(device)
    labels = torch.stack([example.label for example in examples]).to(device)
    logits = model(input_ids, attention_mask, numeric_features)
    loss = F.binary_cross_entropy_with_logits(logits, labels)
    predictions = (torch.sigmoid(logits) >= 0.5).float()
    accuracy = (predictions == labels).float().mean().item()
    model.train()
    return {"loss": loss.item(), "accuracy": accuracy}


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = choose_device(args.device)
    out_dir = ensure_dir(args.out_dir)

    examples = load_examples(args.data_path)
    tokenizer = build_tokenizer(examples)
    suggested_block_size = recommended_block_size(examples, tokenizer)
    block_size = max(args.block_size, suggested_block_size)
    encoded_examples = build_dataset(examples, tokenizer, block_size)

    config = VerifierConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=block_size,
        n_embed=args.n_embed,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
    )
    model = MiniVerifier(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    print(
        f"device={device} vocab={tokenizer.vocab_size} block_size={block_size} "
        f"suggested_block_size={suggested_block_size} examples={len(encoded_examples)} "
        f"params={sum(p.numel() for p in model.parameters()):,}"
    )

    for step in range(args.max_iters):
        if step % args.eval_interval == 0 or step == args.max_iters - 1:
            metrics = evaluate(model, encoded_examples, device)
            print(
                f"step {step}: loss={metrics['loss']:.4f} "
                f"accuracy={metrics['accuracy']:.3f}"
            )

        input_ids, attention_mask, numeric_features, labels = sample_batch(
            encoded_examples,
            args.batch_size,
            device,
        )
        logits = model(input_ids, attention_mask, numeric_features)
        loss = F.binary_cross_entropy_with_logits(logits, labels)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    tokenizer_path = out_dir / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    checkpoint_path = out_dir / "ckpt.pt"
    torch.save(
        {
            "model_state": model.state_dict(),
            "model_config": asdict(config),
            "training_config": vars(args),
            "tokenizer_path": str(tokenizer_path),
        },
        checkpoint_path,
    )
    write_json(
        out_dir / "train_state.json",
        {
            "checkpoint": str(checkpoint_path),
            "tokenizer": str(tokenizer_path),
            "device": device,
            "training_config": vars(args),
            "model_config": asdict(config),
            "suggested_block_size": suggested_block_size,
            "examples": len(encoded_examples),
        },
    )


if __name__ == "__main__":
    main()
