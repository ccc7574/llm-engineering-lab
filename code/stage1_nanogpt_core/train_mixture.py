from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io import write_json
from common.runtime import choose_device, ensure_dir, set_seed
from stage1_nanogpt_core.config import TrainingConfig
from stage1_nanogpt_core.data import get_batch, split_train_val
from stage1_nanogpt_core.model import GPTConfig, MiniGPT
from stage1_nanogpt_core.train import estimate_loss
from common.tokenizer import CharTokenizer


def ensure_min_tokens(tokens: torch.Tensor, block_size: int) -> torch.Tensor:
    if len(tokens) > block_size + 1:
        return tokens
    repeats = ((block_size + 2) // max(len(tokens), 1)) + 1
    return tokens.repeat(repeats)


def parse_args() -> argparse.Namespace:
    defaults = TrainingConfig()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-path", default="datasets/tiny_pretraining_mixture/uniform.json")
    parser.add_argument("--out-dir", default="runs/stage1_mixture")
    for field_name, field_value in asdict(defaults).items():
        if field_name in {"data_path", "out_dir"}:
            continue
        arg_name = f"--{field_name.replace('_', '-')}"
        if isinstance(field_value, bool):
            parser.add_argument(arg_name, action="store_true", default=field_value)
        elif field_value is None:
            parser.add_argument(arg_name, default=None)
        else:
            parser.add_argument(arg_name, type=type(field_value), default=field_value)
    return parser.parse_args()


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_lines(path: str | Path) -> list[str]:
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def build_mixture_text(manifest: dict) -> tuple[str, dict[str, int]]:
    rounds = int(manifest.get("rounds", 12))
    sources = list(manifest["sources"])
    line_pools = {source["name"]: read_lines(source["path"]) for source in sources}
    indices = {source["name"]: 0 for source in sources}
    usage_counts = {source["name"]: 0 for source in sources}
    rendered_lines: list[str] = []

    for _ in range(rounds):
        for source in sources:
            name = str(source["name"])
            weight = int(source.get("weight", 1))
            lines = line_pools[name]
            for _ in range(weight):
                line = lines[indices[name] % len(lines)]
                indices[name] += 1
                usage_counts[name] += 1
                rendered_lines.append(line)

    return "\n".join(rendered_lines) + "\n", usage_counts


@torch.no_grad()
def evaluate_named_sets(
    model: MiniGPT,
    tokenizer: CharTokenizer,
    source_specs: list[dict],
    batch_size: int,
    block_size: int,
    eval_iters: int,
    device: str,
) -> dict[str, float]:
    losses: dict[str, float] = {}
    model.eval()
    for source in source_specs:
        name = str(source["name"])
        text = Path(source["path"]).read_text(encoding="utf-8")
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
        losses[name] = float(metrics["val"])
    model.train()
    return losses


def main() -> None:
    args = parse_args()
    config_payload = {key: value for key, value in vars(args).items() if key not in {"manifest_path"}}
    config_payload["data_path"] = str(args.manifest_path)
    config = TrainingConfig(**config_payload)
    set_seed(config.seed)
    device = choose_device(config.device)
    out_dir = ensure_dir(args.out_dir)

    manifest = load_manifest(args.manifest_path)
    mixture_text, usage_counts = build_mixture_text(manifest)
    tokenizer = CharTokenizer.build(mixture_text)
    tokens = ensure_min_tokens(torch.tensor(tokenizer.encode(mixture_text), dtype=torch.long), config.block_size)
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
        f"device={device} manifest={manifest.get('name', 'mixture')} "
        f"vocab={tokenizer.vocab_size} rendered_lines={sum(usage_counts.values())}"
    )
    final_loss = {"train": 0.0, "val": 0.0}
    for step in range(config.max_iters):
        if step % config.eval_interval == 0 or step == config.max_iters - 1:
            final_loss = estimate_loss(
                model,
                train_data,
                val_data,
                batch_size=config.batch_size,
                block_size=config.block_size,
                eval_iters=config.eval_iters,
                device=device,
            )
            print(f"step {step}: train_loss={final_loss['train']:.4f} val_loss={final_loss['val']:.4f}")
        xb, yb = get_batch(train_data, config.batch_size, config.block_size, device)
        _, loss, _ = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    tokenizer_path = out_dir / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    checkpoint_path = out_dir / "ckpt.pt"
    mixture_path = out_dir / "rendered_mixture.txt"
    mixture_path.write_text(mixture_text, encoding="utf-8")
    source_eval_losses = evaluate_named_sets(
        model,
        tokenizer,
        list(manifest["sources"]),
        batch_size=config.batch_size,
        block_size=config.block_size,
        eval_iters=config.eval_iters,
        device=device,
    )
    torch.save(
        {
            "model_state": model.state_dict(),
            "model_config": model_config.__dict__,
            "training_config": config.to_dict(),
            "tokenizer_path": str(tokenizer_path),
            "manifest_path": str(args.manifest_path),
            "mixture_name": manifest.get("name", "mixture"),
            "source_eval_losses": source_eval_losses,
        },
        checkpoint_path,
    )
    write_json(
        out_dir / "train_state.json",
        {
            "checkpoint": str(checkpoint_path),
            "tokenizer": str(tokenizer_path),
            "mixture_name": manifest.get("name", "mixture"),
            "manifest_path": str(args.manifest_path),
            "rendered_mixture_path": str(mixture_path),
            "usage_counts": usage_counts,
            "source_eval_losses": source_eval_losses,
            "device": device,
            "training_config": config.to_dict(),
            "final_loss": final_loss,
        },
    )
    print(f"source_eval_losses={json.dumps(source_eval_losses, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
