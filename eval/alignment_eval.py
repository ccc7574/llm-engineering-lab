from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.runtime import choose_device, ensure_dir
from stage1_nanogpt_core.model import MiniGPT
from stage5_toy_alignment.dataset import (
    build_preference_pairs,
    collect_training_text,
    load_preference_examples,
    recommended_block_size,
)
from stage5_toy_alignment.utils import (
    build_model_config,
    evaluate_preference_pairs,
    initialize_from_checkpoint,
    load_checkpoint,
    prepare_tokenizer,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--reference-checkpoint", default=None)
    parser.add_argument("--data-path", default="datasets/tiny_preferences/train.jsonl")
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--device", default=None)
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    reference_checkpoint_path = args.reference_checkpoint or args.checkpoint

    examples = load_preference_examples(args.data_path)
    training_text = collect_training_text(examples)
    policy_checkpoint, policy_tokenizer = load_checkpoint(args.checkpoint, device)
    reference_checkpoint, _ = load_checkpoint(reference_checkpoint_path, device)

    tokenizer, added_chars = prepare_tokenizer(policy_tokenizer, training_text)
    block_size = recommended_block_size(examples, tokenizer)
    model_config = build_model_config(policy_checkpoint, tokenizer, block_size, dropout=None)
    pairs = build_preference_pairs(examples, tokenizer, model_config.block_size)

    policy_model = MiniGPT(model_config).to(device)
    reference_model = MiniGPT(model_config).to(device)
    initialize_from_checkpoint(policy_model, policy_checkpoint)
    initialize_from_checkpoint(reference_model, reference_checkpoint)
    policy_model.eval()
    reference_model.eval()

    metrics = evaluate_preference_pairs(policy_model, reference_model, pairs, device, args.beta)
    summary = {
        "checkpoint": args.checkpoint,
        "reference_checkpoint": reference_checkpoint_path,
        "data_path": args.data_path,
        "device": device,
        "added_chars": added_chars,
        "method": policy_checkpoint.get("method", "checkpoint_eval"),
        **metrics,
    }

    print(f"checkpoint={args.checkpoint}")
    print(f"reference_checkpoint={reference_checkpoint_path}")
    print(f"pair_count={summary['pair_count']}")
    print(f"policy_chosen_win_rate={summary['policy_chosen_win_rate']:.3f}")
    print(f"reference_chosen_win_rate={summary['reference_chosen_win_rate']:.3f}")
    print(f"chosen_win_rate_delta={summary['chosen_win_rate_delta']:+.3f}")
    print(f"mean_policy_margin={summary['mean_policy_margin']:.4f}")
    print(f"mean_reference_margin={summary['mean_reference_margin']:.4f}")
    print(f"mean_preference_margin={summary['mean_preference_margin']:+.4f}")
    print(f"mean_kl_proxy={summary['mean_kl_proxy']:.6f}")
    print(f"dpo_loss={summary['dpo_loss']:.4f}")

    if args.report_path:
        report_path = Path(args.report_path)
        ensure_dir(report_path.parent)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved report to {report_path}")


if __name__ == "__main__":
    main()
