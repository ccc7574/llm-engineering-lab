from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io import write_json
from common.runtime import choose_device, ensure_dir, set_seed
from stage1_nanogpt_core.config import TrainingConfig
from stage1_nanogpt_core.data import get_batch, load_char_dataset, split_train_val
from stage1_nanogpt_core.model import GPTConfig, MiniGPT


def parse_args() -> argparse.Namespace:
    defaults = TrainingConfig()
    parser = argparse.ArgumentParser()
    for field_name, field_value in asdict(defaults).items():
        arg_name = f"--{field_name.replace('_', '-')}"
        if isinstance(field_value, bool):
            parser.add_argument(arg_name, action="store_true", default=field_value)
        elif field_value is None:
            parser.add_argument(arg_name, default=None)
        else:
            parser.add_argument(arg_name, type=type(field_value), default=field_value)
    return parser.parse_args()


@torch.no_grad()
def estimate_loss(
    model: MiniGPT,
    train_data: torch.Tensor,
    val_data: torch.Tensor,
    batch_size: int,
    block_size: int,
    eval_iters: int,
    device: str,
) -> dict[str, float]:
    model.eval()
    metrics = {}
    for split_name, split_data in (("train", train_data), ("val", val_data)):
        losses = torch.zeros(eval_iters)
        for step in range(eval_iters):
            xb, yb = get_batch(split_data, batch_size, block_size, device)
            _, loss, _ = model(xb, yb)
            losses[step] = loss.item()
        metrics[split_name] = losses.mean().item()
    model.train()
    return metrics


def main() -> None:
    args = parse_args()
    config = TrainingConfig(**vars(args))
    set_seed(config.seed)
    device = choose_device(config.device)
    out_dir = ensure_dir(config.out_dir)

    _, tokenizer, tokens = load_char_dataset(config.data_path)
    train_data, val_data = split_train_val(tokens)
    model_config = GPTConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=config.block_size,
        n_embed=config.n_embed,
        n_head=config.n_head,
        n_layer=config.n_layer,
        dropout=config.dropout,
    )
    model = MiniGPT(model_config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)

    print(
        f"device={device} vocab={tokenizer.vocab_size} "
        f"params={sum(p.numel() for p in model.parameters()):,}"
    )
    for step in range(config.max_iters):
        if step % config.eval_interval == 0 or step == config.max_iters - 1:
            losses = estimate_loss(
                model,
                train_data,
                val_data,
                batch_size=config.batch_size,
                block_size=config.block_size,
                eval_iters=config.eval_iters,
                device=device,
            )
            print(f"step {step}: train_loss={losses['train']:.4f} val_loss={losses['val']:.4f}")

        xb, yb = get_batch(train_data, config.batch_size, config.block_size, device)
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
            "training_config": config.to_dict(),
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
            "training_config": config.to_dict(),
        },
    )


if __name__ == "__main__":
    main()
