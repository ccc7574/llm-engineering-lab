from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import choose_device
from common.tokenizer import CharTokenizer
from stage0_bigram.train_bigram import BigramLanguageModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="runs/stage0_bigram/ckpt.pt")
    parser.add_argument("--start", default="The ")
    parser.add_argument("--max-new-tokens", type=int, default=200)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    checkpoint = torch.load(args.checkpoint, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    model = BigramLanguageModel(checkpoint["vocab_size"]).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    prompt = torch.tensor([tokenizer.encode(args.start)], dtype=torch.long, device=device)
    output = model.generate(prompt, max_new_tokens=args.max_new_tokens)[0].tolist()
    print(tokenizer.decode(output))


if __name__ == "__main__":
    main()
