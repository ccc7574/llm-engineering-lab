from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch.nn import functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import choose_device, ensure_dir
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.model import GPTConfig, MiniGPT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="runs/stage1_gpt/ckpt.pt")
    parser.add_argument("--start", default="Incident ")
    parser.add_argument("--compare-start", default=None)
    parser.add_argument("--max-new-tokens", type=int, default=200)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--context-window", type=int, default=None)
    parser.add_argument("--report-path", default=None)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def clamp_prompt(
    prompt_ids: list[int],
    block_size: int,
    context_window: int | None,
) -> tuple[list[int], int]:
    effective_window = block_size if context_window is None else min(context_window, block_size)
    if effective_window <= 0:
        raise ValueError("context_window must be positive")
    if len(prompt_ids) <= effective_window:
        return prompt_ids, effective_window
    return prompt_ids[-effective_window:], effective_window


def format_token(token: str) -> str:
    mapping = {
        " ": "<space>",
        "\n": "<newline>",
        "\t": "<tab>",
    }
    return mapping.get(token, token)


def summarize_prompt(
    model: MiniGPT,
    tokenizer: CharTokenizer,
    raw_prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    context_window: int | None,
    device: str,
) -> tuple[str, str]:
    prompt_ids = tokenizer.encode(raw_prompt)
    used_prompt_ids, effective_window = clamp_prompt(prompt_ids, model.config.block_size, context_window)
    truncated = len(used_prompt_ids) != len(prompt_ids)
    prompt = torch.tensor([used_prompt_ids], dtype=torch.long, device=device)

    with torch.no_grad():
        logits, _, _ = model(prompt)
        next_token_logits = logits[0, -1, :]
        next_token_probs = F.softmax(next_token_logits, dim=-1)
        top_values, top_indices = torch.topk(next_token_probs, min(top_k, next_token_probs.numel()))
        generated = model.generate(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
        )[0].tolist()

    lines = [
        f"Prompt: {raw_prompt}",
        f"Context used: {tokenizer.decode(used_prompt_ids)}",
        f"Prompt length: {len(prompt_ids)} tokens",
        f"Effective context window: {effective_window}",
        f"Truncated to fit window: {truncated}",
        "Top next-token predictions:",
    ]
    for rank, (token_id, prob) in enumerate(zip(top_indices.tolist(), top_values.tolist()), start=1):
        token = tokenizer.decode([token_id])
        lines.append(f"  {rank:>2}. {format_token(token)!r} prob={prob:.3f}")
    lines.extend(
        [
            "",
            "Sampled continuation:",
            tokenizer.decode(generated),
        ]
    )
    return "\n".join(lines), tokenizer.decode(used_prompt_ids)


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    checkpoint = torch.load(args.checkpoint, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    model = MiniGPT(GPTConfig(**checkpoint["model_config"])).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    first_report, first_context = summarize_prompt(
            model=model,
            tokenizer=tokenizer,
            raw_prompt=args.start,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            context_window=args.context_window,
            device=device,
        )
    reports = [first_report]
    if args.compare_start:
        second_report, second_context = summarize_prompt(
                model=model,
                tokenizer=tokenizer,
                raw_prompt=args.compare_start,
                max_new_tokens=args.max_new_tokens,
                temperature=args.temperature,
                top_k=args.top_k,
                context_window=args.context_window,
                device=device,
            )
        reports.append(second_report)

        note = None
        if args.start != args.compare_start and first_context == second_context:
            note = (
                "Note: the two prompts collapse to the same effective context window. "
                "If the predictions match, that is evidence that the clipped-away prefix is no longer available."
            )
        if note:
            reports.insert(0, note)

    separator = "\n\n" + ("-" * 72) + "\n\n"
    rendered = separator.join(reports)
    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(rendered, encoding="utf-8")
        print(f"saved comparison report to {report_path}")
    print(rendered)


if __name__ == "__main__":
    main()
