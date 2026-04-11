from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io import write_json
from common.runtime import choose_device, ensure_dir, set_seed
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.data import get_batch, split_train_val
from stage1_nanogpt_core.model import GPTConfig, MiniGPT
from stage1_nanogpt_core.train import estimate_loss


def ensure_min_tokens(tokens: torch.Tensor, block_size: int) -> torch.Tensor:
    if len(tokens) > block_size + 1:
        return tokens
    repeats = ((block_size + 2) // max(len(tokens), 1)) + 1
    return tokens.repeat(repeats)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="runs/stage1_gpt/ckpt.pt")
    parser.add_argument("--data-path", default="datasets/tiny_pretraining_payments/input.txt")
    parser.add_argument("--eval-set", action="append", default=[])
    parser.add_argument("--out-dir", default="runs/stage1_domain_adapted")
    parser.add_argument("--max-iters", type=int, default=120)
    parser.add_argument("--eval-interval", type=int, default=30)
    parser.add_argument("--eval-iters", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def parse_eval_sets(raw_sets: list[str], default_domain_path: str) -> list[tuple[str, str]]:
    if not raw_sets:
        return [("domain", default_domain_path)]
    parsed: list[tuple[str, str]] = []
    for raw in raw_sets:
        if "=" not in raw:
            raise ValueError(f"invalid --eval-set {raw!r}, expected label=path")
        label, path = raw.split("=", 1)
        parsed.append((label.strip(), path.strip()))
    return parsed


@torch.no_grad()
def evaluate_sets(
    model: MiniGPT,
    tokenizer: CharTokenizer,
    eval_sets: list[tuple[str, str]],
    batch_size: int,
    block_size: int,
    eval_iters: int,
    device: str,
) -> dict[str, float]:
    losses: dict[str, float] = {}
    model.eval()
    for label, path in eval_sets:
        text = Path(path).read_text(encoding="utf-8")
        tokens = ensure_min_tokens(torch.tensor(tokenizer.encode(text), dtype=torch.long), block_size)
        train_data, val_data = split_train_val(tokens)
        metrics = estimate_loss(
            model,
            train_data,
            val_data,
            batch_size=batch_size,
            block_size=block_size,
            eval_iters=eval_iters,
            device=device,
        )
        losses[label] = float(metrics["val"])
    model.train()
    return losses


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = choose_device(args.device)
    out_dir = ensure_dir(args.out_dir)

    checkpoint = torch.load(args.checkpoint, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    tokenizer_path = out_dir / "tokenizer.json"
    shutil.copyfile(checkpoint["tokenizer_path"], tokenizer_path)

    model = MiniGPT(GPTConfig(**checkpoint["model_config"])).to(device)
    model.load_state_dict(checkpoint["model_state"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    domain_text = Path(args.data_path).read_text(encoding="utf-8")
    domain_tokens = ensure_min_tokens(
        torch.tensor(tokenizer.encode(domain_text), dtype=torch.long),
        int(checkpoint["model_config"]["block_size"]),
    )
    train_data, val_data = split_train_val(domain_tokens)
    eval_sets = parse_eval_sets(args.eval_set, args.data_path)
    base_eval_losses = evaluate_sets(
        model,
        tokenizer,
        eval_sets,
        batch_size=args.batch_size,
        block_size=model.config.block_size,
        eval_iters=args.eval_iters,
        device=device,
    )

    print(
        f"device={device} init_from={args.checkpoint} "
        f"domain_chars={len(domain_text)} eval_sets={json.dumps(dict(eval_sets), ensure_ascii=False)}"
    )
    final_loss = {"train": 0.0, "val": 0.0}
    for step in range(args.max_iters):
        if step % args.eval_interval == 0 or step == args.max_iters - 1:
            final_loss = estimate_loss(
                model,
                train_data,
                val_data,
                batch_size=args.batch_size,
                block_size=model.config.block_size,
                eval_iters=args.eval_iters,
                device=device,
            )
            print(f"step {step}: train_loss={final_loss['train']:.4f} val_loss={final_loss['val']:.4f}")
        xb, yb = get_batch(train_data, args.batch_size, model.config.block_size, device)
        _, loss, _ = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    adapted_eval_losses = evaluate_sets(
        model,
        tokenizer,
        eval_sets,
        batch_size=args.batch_size,
        block_size=model.config.block_size,
        eval_iters=args.eval_iters,
        device=device,
    )
    loss_deltas = {label: adapted_eval_losses[label] - base_eval_losses[label] for label, _ in eval_sets}

    checkpoint_path = out_dir / "ckpt.pt"
    torch.save(
        {
            "model_state": model.state_dict(),
            "model_config": checkpoint["model_config"],
            "training_config": {
                "init_from": args.checkpoint,
                "data_path": args.data_path,
                "eval_sets": dict(eval_sets),
                "max_iters": args.max_iters,
                "eval_interval": args.eval_interval,
                "eval_iters": args.eval_iters,
                "batch_size": args.batch_size,
                "learning_rate": args.learning_rate,
                "seed": args.seed,
            },
            "tokenizer_path": str(tokenizer_path),
            "base_eval_losses": base_eval_losses,
            "adapted_eval_losses": adapted_eval_losses,
            "loss_deltas": loss_deltas,
        },
        checkpoint_path,
    )
    write_json(
        out_dir / "train_state.json",
        {
            "checkpoint": str(checkpoint_path),
            "tokenizer": str(tokenizer_path),
            "init_from": args.checkpoint,
            "data_path": args.data_path,
            "eval_sets": dict(eval_sets),
            "base_eval_losses": base_eval_losses,
            "adapted_eval_losses": adapted_eval_losses,
            "loss_deltas": loss_deltas,
            "device": device,
            "final_domain_loss": final_loss,
        },
    )
    print(f"base_eval_losses={json.dumps(base_eval_losses, ensure_ascii=False)}")
    print(f"adapted_eval_losses={json.dumps(adapted_eval_losses, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
