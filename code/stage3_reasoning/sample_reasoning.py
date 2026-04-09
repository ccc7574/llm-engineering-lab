from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import choose_device, set_seed
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.model import GPTConfig, MiniGPT
from stage3_reasoning.self_consistency import choose_consensus, render_candidate_for_verifier, sample_candidates
from stage4_verifier.rerank import load_model as load_verifier_model
from stage4_verifier.rerank import rerank_candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="runs/stage2_sft/ckpt.pt")
    parser.add_argument("--question", required=True)
    parser.add_argument("--num-samples", type=int, default=5)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--verifier-checkpoint", default=None)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def load_model(checkpoint_path: str, device: str) -> tuple[MiniGPT, CharTokenizer]:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    tokenizer = CharTokenizer.load(checkpoint["tokenizer_path"])
    model = MiniGPT(GPTConfig(**checkpoint["model_config"])).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, tokenizer


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    device = choose_device(args.device)
    model, tokenizer = load_model(args.checkpoint, device)
    verifier = None
    if args.verifier_checkpoint:
        verifier = load_verifier_model(args.verifier_checkpoint, device)

    candidates = sample_candidates(
        model=model,
        tokenizer=tokenizer,
        question=args.question,
        num_samples=args.num_samples,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        device=device,
    )
    consensus = choose_consensus(candidates)
    verifier_ranking = None
    if verifier is not None:
        verifier_model, verifier_tokenizer = verifier
        verifier_ranking = rerank_candidates(
            verifier_model,
            verifier_tokenizer,
            f"Question: {args.question}",
            [render_candidate_for_verifier(candidate) for candidate in candidates],
            device,
        )

    print(f"Question: {args.question}")
    print(
        f"Consensus answer: {consensus.answer} "
        f"(support {consensus.support}/{consensus.total_candidates})"
    )
    if verifier_ranking:
        print(
            f"Verifier top candidate score={verifier_ranking[0].score:.3f} "
            f"text={verifier_ranking[0].candidate}"
        )
    print("=" * 72)
    for index, candidate in enumerate(candidates, start=1):
        parsed = candidate.final_answer or "[unparsed]"
        verifier_suffix = ""
        if verifier_ranking:
            match = next(
                (item for item in verifier_ranking if item.candidate == candidate.text),
                None,
            )
            if match is None:
                rendered = render_candidate_for_verifier(candidate)
                match = next((item for item in verifier_ranking if item.candidate == rendered), None)
            if match is not None:
                verifier_suffix = f" | verifier_score={match.score:.3f}"
        print(
            f"Candidate {index} | answer={parsed} | generated_tokens={candidate.generated_tokens}"
            f"{verifier_suffix}"
        )
        print(candidate.text.strip() or "[empty generation]")
        print("-" * 72)


if __name__ == "__main__":
    main()
