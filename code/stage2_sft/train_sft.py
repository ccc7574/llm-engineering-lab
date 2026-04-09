from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io import write_json
from common.runtime import choose_device, ensure_dir, set_seed
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.model import GPTConfig, MiniGPT
from stage2_sft.dataset import (
    build_windows,
    collect_training_text,
    extend_tokenizer,
    load_sft_examples,
    recommended_block_size,
    sample_batch,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", nargs="+", default=["datasets/tiny_sft/train.jsonl"])
    parser.add_argument("--eval-path", nargs="+", default=["datasets/tiny_sft/eval.jsonl"])
    parser.add_argument("--init-from", default="runs/stage1_gpt/ckpt.pt")
    parser.add_argument("--out-dir", default="runs/stage2_sft")
    parser.add_argument("--max-iters", type=int, default=300)
    parser.add_argument("--eval-interval", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--block-size", type=int, default=192)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=None)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def load_checkpoint(path: str, device: str) -> tuple[dict, CharTokenizer]:
    checkpoint = torch.load(path, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    return checkpoint, tokenizer


def build_model_config(args: argparse.Namespace, checkpoint: dict, tokenizer: CharTokenizer) -> GPTConfig:
    base_config = checkpoint["model_config"]
    return GPTConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=max(args.block_size, base_config["block_size"]),
        n_embed=base_config["n_embed"],
        n_head=base_config["n_head"],
        n_layer=base_config["n_layer"],
        dropout=base_config["dropout"] if args.dropout is None else args.dropout,
    )


def initialize_from_checkpoint(model: MiniGPT, checkpoint: dict) -> None:
    source_state = checkpoint["model_state"]
    target_state = model.state_dict()
    copied_keys = []
    resized_keys = []

    for key, source_value in source_state.items():
        if key not in target_state:
            continue
        target_value = target_state[key]
        if source_value.shape == target_value.shape:
            target_state[key] = source_value
            copied_keys.append(key)
            continue

        if key in {"token_embedding.weight", "lm_head.weight"} and source_value.ndim == 2:
            rows = min(source_value.shape[0], target_value.shape[0])
            cols = min(source_value.shape[1], target_value.shape[1])
            target_value[:rows, :cols] = source_value[:rows, :cols]
            resized_keys.append(key)
            continue

        if key == "lm_head.bias" and source_value.ndim == 1:
            rows = min(source_value.shape[0], target_value.shape[0])
            target_value[:rows] = source_value[:rows]
            resized_keys.append(key)
            continue

        if key == "position_embedding.weight" and source_value.ndim == 2:
            rows = min(source_value.shape[0], target_value.shape[0])
            cols = min(source_value.shape[1], target_value.shape[1])
            target_value[:rows, :cols] = source_value[:rows, :cols]
            resized_keys.append(key)
            continue

        if key.endswith(".attn.mask") and source_value.ndim == 2:
            rows = min(source_value.shape[0], target_value.shape[0])
            cols = min(source_value.shape[1], target_value.shape[1])
            target_value[:rows, :cols] = source_value[:rows, :cols]
            resized_keys.append(key)

    model.load_state_dict(target_state)
    print(f"loaded {len(copied_keys)} tensors and resized {len(resized_keys)} tensors from base checkpoint")


@torch.no_grad()
def estimate_loss(
    model: MiniGPT,
    windows: list,
    batch_size: int,
    device: str,
) -> float:
    model.eval()
    losses = []
    for start in range(0, len(windows), batch_size):
        batch = windows[start : start + batch_size]
        xb = torch.stack([window.input_ids for window in batch]).to(device)
        yb = torch.stack([window.labels for window in batch]).to(device)
        _, loss, _ = model(xb, yb)
        losses.append(loss.item())
    model.train()
    return sum(losses) / max(len(losses), 1)


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = choose_device(args.device)
    out_dir = ensure_dir(args.out_dir)

    train_examples = load_sft_examples(args.data_path)
    eval_examples = load_sft_examples(args.eval_path)
    base_checkpoint, base_tokenizer = load_checkpoint(args.init_from, device)

    tokenizer_text = collect_training_text(train_examples + eval_examples)
    tokenizer, added_chars = extend_tokenizer(base_tokenizer, tokenizer_text)
    model_config = build_model_config(args, base_checkpoint, tokenizer)
    suggested_block_size = recommended_block_size(train_examples + eval_examples, tokenizer)
    model_config.block_size = max(model_config.block_size, suggested_block_size)

    train_windows = build_windows(train_examples, tokenizer, model_config.block_size)
    eval_windows = build_windows(eval_examples, tokenizer, model_config.block_size)

    model = MiniGPT(model_config).to(device)
    initialize_from_checkpoint(model, base_checkpoint)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    print(
        f"device={device} vocab={tokenizer.vocab_size} added_chars={len(added_chars)} "
        f"block_size={model_config.block_size} suggested_block_size={suggested_block_size} "
        f"train_examples={len(train_examples)} "
        f"eval_examples={len(eval_examples)} train_windows={len(train_windows)} "
        f"eval_windows={len(eval_windows)} params={sum(p.numel() for p in model.parameters()):,}"
    )

    for step in range(args.max_iters):
        if step % args.eval_interval == 0 or step == args.max_iters - 1:
            train_loss = estimate_loss(model, train_windows, args.batch_size, device)
            eval_loss = estimate_loss(model, eval_windows, args.batch_size, device)
            print(f"step {step}: train_loss={train_loss:.4f} eval_loss={eval_loss:.4f}")

        xb, yb = sample_batch(train_windows, args.batch_size, device)
        _, loss, _ = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    tokenizer_path = out_dir / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    checkpoint_path = out_dir / "ckpt.pt"
    torch.save(
        {
            "model_state": model.state_dict(),
            "model_config": model_config.__dict__,
            "training_config": vars(args),
            "tokenizer_path": str(tokenizer_path),
            "init_from": args.init_from,
            "added_chars": added_chars,
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
            "added_chars": added_chars,
            "model_config": model_config.__dict__,
            "suggested_block_size": suggested_block_size,
            "train_examples": len(train_examples),
            "eval_examples": len(eval_examples),
            "train_windows": len(train_windows),
            "eval_windows": len(eval_windows),
        },
    )


if __name__ == "__main__":
    main()
