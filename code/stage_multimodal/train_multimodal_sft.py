from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io import write_json
from common.runtime import choose_device, ensure_dir, set_seed
from stage_multimodal.router_sft import (
    ROUTE_LABELS,
    LinearRoutePolicy,
    build_feature_vocab,
    label_counts,
    label_tensor,
    load_route_tasks,
    vectorize_tasks,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_multimodal_sft/train.jsonl")
    parser.add_argument("--out-dir", default="runs/multimodal_sft_router")
    parser.add_argument("--max-iters", type=int, default=200)
    parser.add_argument("--eval-interval", type=int, default=50)
    parser.add_argument("--learning-rate", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    predictions = torch.argmax(logits, dim=1)
    return float((predictions == labels).float().mean().item())


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = choose_device(args.device)
    out_dir = ensure_dir(args.out_dir)

    tasks = load_route_tasks(args.data_path)
    feature_vocab = build_feature_vocab(tasks)
    inputs = vectorize_tasks(tasks, feature_vocab).to(device)
    labels = label_tensor(tasks).to(device)

    model = LinearRoutePolicy(inputs.shape[1], len(ROUTE_LABELS)).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    loss_fn = nn.CrossEntropyLoss()

    print(
        f"device={device} train_examples={len(tasks)} "
        f"feature_vocab={len(feature_vocab)} labels={json.dumps(label_counts(tasks), ensure_ascii=False)}"
    )

    final_loss = 0.0
    final_accuracy = 0.0
    for step in range(args.max_iters):
        logits = model(inputs)
        loss = loss_fn(logits, labels)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

        if step % args.eval_interval == 0 or step == args.max_iters - 1:
            with torch.no_grad():
                eval_logits = model(inputs)
                final_loss = float(loss_fn(eval_logits, labels).item())
                final_accuracy = accuracy(eval_logits, labels)
            print(f"step {step}: loss={final_loss:.4f} route_accuracy={final_accuracy:.3f}")

    checkpoint_path = out_dir / "router.pt"
    train_state_path = out_dir / "train_state.json"
    torch.save(
        {
            "model_state": model.state_dict(),
            "feature_vocab": feature_vocab,
            "labels": ROUTE_LABELS,
            "training_config": vars(args),
            "final_metrics": {
                "route_accuracy": final_accuracy,
                "cross_entropy_loss": final_loss,
                "feature_vocab_size": len(feature_vocab),
                "train_examples": len(tasks),
            },
        },
        checkpoint_path,
    )
    write_json(
        train_state_path,
        {
            "method": "multimodal_route_sft",
            "training_config": vars(args),
            "label_counts": label_counts(tasks),
            "final_metrics": {
                "route_accuracy": final_accuracy,
                "cross_entropy_loss": final_loss,
                "feature_vocab_size": len(feature_vocab),
                "train_examples": len(tasks),
            },
            "checkpoint_path": str(checkpoint_path),
        },
    )
    print(f"saved checkpoint to {checkpoint_path}")
    print(f"saved train state to {train_state_path}")


if __name__ == "__main__":
    main()
