from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import choose_device
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.data import decode_window, get_batch, load_char_dataset
from stage1_nanogpt_core.model import GPTConfig, MiniGPT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_shakespeare/input.txt")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=24)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def print_xy(tokenizer: CharTokenizer, x: torch.Tensor, y: torch.Tensor) -> None:
    for row_index in range(x.size(0)):
        x_tokens = decode_window(tokenizer, x[row_index])
        y_tokens = decode_window(tokenizer, y[row_index])
        print(f"\nBatch row {row_index}")
        for pos, (src_id, tgt_id, src_token, tgt_token) in enumerate(
            zip(x[row_index].tolist(), y[row_index].tolist(), x_tokens, y_tokens)
        ):
            print(
                f"pos={pos:02d} "
                f"x_id={src_id:03d} x_tok={src_token!r} "
                f"-> y_id={tgt_id:03d} y_tok={tgt_token!r}"
            )


@torch.no_grad()
def print_topk_predictions(
    model: MiniGPT,
    tokenizer: CharTokenizer,
    x: torch.Tensor,
    y: torch.Tensor,
    top_k: int = 5,
) -> None:
    logits, _, _ = model(x)
    print("\nTop-k predictions for the first batch row")
    for pos in range(min(8, x.size(1))):
        probs = torch.softmax(logits[0, pos], dim=-1)
        values, indices = torch.topk(probs, k=top_k)
        expected = tokenizer.decode([int(y[0, pos])])
        formatted = ", ".join(
            f"{tokenizer.decode([int(idx)])!r}:{float(val):.3f}"
            for val, idx in zip(values, indices)
        )
        print(f"pos={pos:02d} expected={expected!r} predictions=[{formatted}]")


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    _, tokenizer, tokens = load_char_dataset(args.data_path)
    x, y = get_batch(tokens, batch_size=args.batch_size, block_size=args.block_size, device=device)
    print_xy(tokenizer, x.cpu(), y.cpu())

    if args.checkpoint:
        checkpoint = torch.load(args.checkpoint, map_location=device)
        model = MiniGPT(GPTConfig(**checkpoint["model_config"])).to(device)
        model.load_state_dict(checkpoint["model_state"])
        model.eval()
        print_topk_predictions(model, tokenizer, x, y)


if __name__ == "__main__":
    main()
