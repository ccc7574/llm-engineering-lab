from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import choose_device, ensure_dir, set_seed
from common.tokenizer import CharTokenizer


class BigramLanguageModel(nn.Module):
    def __init__(self, vocab_size: int) -> None:
        super().__init__()
        self.table = nn.Embedding(vocab_size, vocab_size)

    def forward(
        self,
        idx: torch.Tensor,
        targets: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        logits = self.table(idx)
        loss = None
        if targets is not None:
            bsz, steps, channels = logits.shape
            loss = F.cross_entropy(logits.view(bsz * steps, channels), targets.view(bsz * steps))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx: torch.Tensor, max_new_tokens: int) -> torch.Tensor:
        for _ in range(max_new_tokens):
            logits, _ = self(idx[:, -1:])
            probs = F.softmax(logits[:, -1, :], dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, next_token), dim=1)
        return idx


def get_batch(data: torch.Tensor, batch_size: int, block_size: int, device: str) -> tuple[torch.Tensor, torch.Tensor]:
    max_start = len(data) - block_size - 1
    starts = torch.randint(0, max_start, (batch_size,))
    x = torch.stack([data[start : start + block_size] for start in starts])
    y = torch.stack([data[start + 1 : start + block_size + 1] for start in starts])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(
    model: BigramLanguageModel,
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
            _, loss = model(xb, yb)
            losses[step] = loss.item()
        metrics[split_name] = losses.mean().item()
    model.train()
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_shakespeare/input.txt")
    parser.add_argument("--out-dir", default="runs/stage0_bigram")
    parser.add_argument("--max-iters", type=int, default=300)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--eval-iters", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-2)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = choose_device(args.device)
    out_dir = ensure_dir(args.out_dir)

    text = Path(args.data_path).read_text(encoding="utf-8")
    tokenizer = CharTokenizer.build(text)
    data = torch.tensor(tokenizer.encode(text), dtype=torch.long)
    split_at = int(0.9 * len(data))
    train_data = data[:split_at]
    val_data = data[split_at:]

    model = BigramLanguageModel(tokenizer.vocab_size).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    print(f"device={device} vocab={tokenizer.vocab_size} train_tokens={len(train_data)} val_tokens={len(val_data)}")
    for step in range(args.max_iters):
        if step % args.eval_interval == 0 or step == args.max_iters - 1:
            losses = estimate_loss(
                model,
                train_data,
                val_data,
                batch_size=args.batch_size,
                block_size=args.block_size,
                eval_iters=args.eval_iters,
                device=device,
            )
            print(f"step {step}: train_loss={losses['train']:.4f} val_loss={losses['val']:.4f}")

        xb, yb = get_batch(train_data, args.batch_size, args.block_size, device)
        _, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    tokenizer.save(out_dir / "tokenizer.json")
    torch.save(
        {
            "model_state": model.state_dict(),
            "vocab_size": tokenizer.vocab_size,
            "tokenizer_path": str(out_dir / "tokenizer.json"),
            "config": vars(args),
        },
        out_dir / "ckpt.pt",
    )

    seed_tokens = torch.zeros((1, 1), dtype=torch.long, device=device)
    preview = tokenizer.decode(model.generate(seed_tokens, max_new_tokens=200)[0].tolist())
    print("\nSample:\n")
    print(preview)


if __name__ == "__main__":
    main()
