from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.io import load_jsonl
from common.runtime import choose_device
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.model import GPTConfig, MiniGPT
from stage2_sft.prompt_template import SFTExample, render_prompt, strip_generation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="runs/stage2_sft/ckpt.pt")
    parser.add_argument("--base-checkpoint", default="runs/stage1_gpt/ckpt.pt")
    parser.add_argument("--data-path", default="datasets/tiny_sft/eval.jsonl")
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def load_model(checkpoint_path: str, device: str) -> tuple[MiniGPT, CharTokenizer]:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    model = MiniGPT(GPTConfig(**checkpoint["model_config"])).to(device)
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


def generate_response(
    model: MiniGPT,
    tokenizer: CharTokenizer,
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    device: str,
) -> str:
    prompt_ids = tokenizer.encode(make_tokenizer_compatible(prompt, tokenizer))
    prompt_tensor = torch.tensor([prompt_ids[-model.config.block_size :]], dtype=torch.long, device=device)
    generated = model.generate(
        prompt_tensor,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
    )[0].tolist()
    completion_ids = generated[len(prompt_tensor[0]) :]
    return strip_generation(tokenizer.decode(completion_ids))


def safe_generate(
    model: MiniGPT,
    tokenizer: CharTokenizer,
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    device: str,
) -> str:
    try:
        return generate_response(model, tokenizer, prompt, max_new_tokens, temperature, top_k, device)
    except ValueError as exc:
        return f"[generation skipped: {exc}]"


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)

    sft_model, sft_tokenizer = load_model(args.checkpoint, device)
    base_model, base_tokenizer = load_model(args.base_checkpoint, device)
    rows = load_jsonl(args.data_path)
    examples = [
        SFTExample(
            instruction=row["instruction"],
            input=row.get("input", ""),
            output=row["output"],
        )
        for row in rows
    ]

    sft_exact = 0
    for index, example in enumerate(examples, start=1):
        prompt = render_prompt(example)
        base_response = safe_generate(
            base_model,
            base_tokenizer,
            prompt,
            args.max_new_tokens,
            args.temperature,
            args.top_k,
            device,
        )
        sft_response = safe_generate(
            sft_model,
            sft_tokenizer,
            prompt,
            args.max_new_tokens,
            args.temperature,
            args.top_k,
            device,
        )
        if sft_response.strip() == example.output.strip():
            sft_exact += 1

        print(f"Example {index}")
        print(f"Instruction: {example.instruction}")
        if example.input:
            print(f"Input: {example.input}")
        print(f"Expected: {example.output}")
        print(f"Base: {base_response}")
        print(f"SFT: {sft_response}")
        print("-" * 72)

    accuracy = sft_exact / max(len(examples), 1)
    print(f"SFT exact_match={accuracy:.3f} ({sft_exact}/{len(examples)})")


if __name__ == "__main__":
    main()
