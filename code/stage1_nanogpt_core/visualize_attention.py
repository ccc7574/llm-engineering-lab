from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import choose_device, ensure_dir
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.model import GPTConfig, MiniGPT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="runs/stage1_gpt/ckpt.pt")
    parser.add_argument("--prompt", default="Question: Why did the deploy fail?")
    parser.add_argument("--output", default="runs/stage1_gpt/attention_report.txt")
    parser.add_argument("--svg-output", default=None)
    parser.add_argument("--head", default="avg")
    parser.add_argument("--context-window", type=int, default=None)
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


def display_token(token: str) -> str:
    mapping = {
        " ": "SP",
        "\n": "\\n",
        "\t": "\\t",
    }
    return mapping.get(token, token)


def format_table(tokens: list[str], matrix: torch.Tensor) -> str:
    lines = []
    header = "tok\t" + "\t".join(repr(display_token(token)) for token in tokens)
    lines.append(header)
    for row_token, row in zip(tokens, matrix.tolist()):
        scores = "\t".join(f"{value:.3f}" for value in row)
        lines.append(f"{display_token(row_token)!r}\t{scores}")
    return "\n".join(lines)


def select_attention_map(attention_maps: list[torch.Tensor], head: str) -> tuple[torch.Tensor, str]:
    final_block = attention_maps[-1][0]
    if head == "avg":
        return final_block.mean(dim=0), "average over all heads"
    head_index = int(head)
    if head_index < 0 or head_index >= final_block.size(0):
        raise ValueError(f"head must be in [0, {final_block.size(0) - 1}]")
    return final_block[head_index], f"head {head_index}"


def attention_color(value: float) -> str:
    start = (247, 250, 255)
    end = (27, 86, 164)
    red = round(start[0] + (end[0] - start[0]) * value)
    green = round(start[1] + (end[1] - start[1]) * value)
    blue = round(start[2] + (end[2] - start[2]) * value)
    return f"rgb({red},{green},{blue})"


def render_svg(tokens: list[str], matrix: torch.Tensor, title: str) -> str:
    cell = 28
    left = 92
    top = 72
    width = left + cell * len(tokens) + 24
    height = top + cell * len(tokens) + 24
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<style>',
        'text { font-family: Menlo, Consolas, monospace; fill: #1f2937; }',
        '.label { font-size: 11px; }',
        '.title { font-size: 14px; font-weight: 600; }',
        '.cell-text { font-size: 9px; fill: #ffffff; }',
        '</style>',
        f'<text x="{left}" y="22" class="title">{html.escape(title)}</text>',
    ]

    for idx, token in enumerate(tokens):
        x = left + idx * cell + cell / 2
        y = top - 14
        label = html.escape(display_token(token))
        parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" class="label">{label}</text>')
        parts.append(
            f'<text x="{left - 10}" y="{top + idx * cell + 18}" text-anchor="end" class="label">{label}</text>'
        )

    for row_index, row in enumerate(matrix.tolist()):
        for col_index, value in enumerate(row):
            x = left + col_index * cell
            y = top + row_index * cell
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                f'fill="{attention_color(value)}" stroke="#d1d5db" stroke-width="0.5" />'
            )
            if value >= 0.15:
                parts.append(
                    f'<text x="{x + cell / 2}" y="{y + 18}" text-anchor="middle" class="cell-text">{value:.2f}</text>'
                )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    checkpoint = torch.load(args.checkpoint, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    model_config = GPTConfig(**checkpoint["model_config"])
    model = MiniGPT(model_config).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    prompt_ids = tokenizer.encode(args.prompt)
    prompt_ids, effective_window = clamp_prompt(prompt_ids, model_config.block_size, args.context_window)
    truncated = len(prompt_ids) != len(tokenizer.encode(args.prompt))
    prompt = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    _, _, attention_maps = model(prompt, need_weights=True)
    if not attention_maps:
        raise RuntimeError("model did not return attention maps")
    selected_map, map_label = select_attention_map(attention_maps, args.head)
    tokens = [tokenizer.decode([token_id]) for token_id in prompt_ids]
    report = [
        f"Prompt: {args.prompt}",
        f"Context used: {tokenizer.decode(prompt_ids)}",
        f"Model block size: {model_config.block_size}",
        f"Effective context window: {effective_window}",
        f"Used tokens: {len(prompt_ids)}",
        f"Truncated to fit window: {truncated}",
        "",
        f"Attention weights from the final transformer block ({map_label}):",
        format_table(tokens, selected_map),
    ]

    output_path = Path(args.output)
    ensure_dir(output_path.parent)
    output_path.write_text("\n".join(report), encoding="utf-8")
    svg_output = Path(args.svg_output) if args.svg_output else output_path.with_suffix(".svg")
    ensure_dir(svg_output.parent)
    svg_output.write_text(
        render_svg(tokens, selected_map, f"Final block attention heatmap ({map_label})"),
        encoding="utf-8",
    )
    print(f"saved attention report to {output_path}")
    print(f"saved attention heatmap to {svg_output}")


if __name__ == "__main__":
    main()
