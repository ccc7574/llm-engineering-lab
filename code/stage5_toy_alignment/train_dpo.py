from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch.nn import functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import choose_device, ensure_dir, set_seed
from stage1_nanogpt_core.model import MiniGPT
from stage5_toy_alignment.dataset import (
    build_preference_pairs,
    collect_training_text,
    load_preference_examples,
    recommended_block_size,
    sample_pair_batch,
)
from stage5_toy_alignment.utils import (
    build_model_config,
    evaluate_preference_pairs,
    format_metrics,
    initialize_from_checkpoint,
    load_checkpoint,
    prepare_tokenizer,
    save_training_outputs,
    sequence_log_probs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_preferences/train.jsonl")
    parser.add_argument("--init-from", default="runs/stage2_sft_smoke/ckpt.pt")
    parser.add_argument("--out-dir", default="runs/stage5_dpo")
    parser.add_argument("--max-iters", type=int, default=120)
    parser.add_argument("--eval-interval", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--dropout", type=float, default=None)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = choose_device(args.device)
    out_dir = ensure_dir(args.out_dir)

    examples = load_preference_examples(args.data_path)
    base_checkpoint, base_tokenizer = load_checkpoint(args.init_from, device)
    tokenizer, added_chars = prepare_tokenizer(base_tokenizer, collect_training_text(examples))
    block_size = recommended_block_size(examples, tokenizer)
    model_config = build_model_config(base_checkpoint, tokenizer, block_size, args.dropout)
    pairs = build_preference_pairs(examples, tokenizer, model_config.block_size)

    policy_model = MiniGPT(model_config).to(device)
    reference_model = MiniGPT(model_config).to(device)
    initialize_from_checkpoint(policy_model, base_checkpoint)
    initialize_from_checkpoint(reference_model, base_checkpoint)
    reference_model.eval()
    for parameter in reference_model.parameters():
        parameter.requires_grad = False

    optimizer = torch.optim.AdamW(policy_model.parameters(), lr=args.learning_rate)
    print(
        f"device={device} pair_count={len(pairs)} vocab={tokenizer.vocab_size} "
        f"block_size={model_config.block_size} beta={args.beta}"
    )

    for step in range(args.max_iters):
        if step % args.eval_interval == 0 or step == args.max_iters - 1:
            metrics = evaluate_preference_pairs(policy_model, reference_model, pairs, device, args.beta)
            print(f"step {step}: {format_metrics(metrics)}")

        chosen_inputs, chosen_labels, rejected_inputs, rejected_labels = sample_pair_batch(
            pairs,
            args.batch_size,
            device,
        )
        policy_chosen = sequence_log_probs(policy_model, chosen_inputs, chosen_labels)
        policy_rejected = sequence_log_probs(policy_model, rejected_inputs, rejected_labels)
        with torch.no_grad():
            ref_chosen = sequence_log_probs(reference_model, chosen_inputs, chosen_labels)
            ref_rejected = sequence_log_probs(reference_model, rejected_inputs, rejected_labels)
        loss = -F.logsigmoid(args.beta * ((policy_chosen - policy_rejected) - (ref_chosen - ref_rejected))).mean()

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    final_metrics = evaluate_preference_pairs(policy_model, reference_model, pairs, device, args.beta)
    tokenizer_path = out_dir / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    checkpoint_path = out_dir / "ckpt.pt"
    torch.save(
        {
            "model_state": policy_model.state_dict(),
            "model_config": model_config.__dict__,
            "training_config": vars(args),
            "tokenizer_path": str(tokenizer_path),
            "init_from": args.init_from,
            "added_chars": added_chars,
            "method": "toy_dpo",
            "final_metrics": final_metrics,
        },
        checkpoint_path,
    )
    save_training_outputs(
        out_dir=out_dir,
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        training_config=vars(args),
        model_config=model_config.__dict__,
        added_chars=added_chars,
        metrics=final_metrics,
        method="toy_dpo",
    )


if __name__ == "__main__":
    main()
