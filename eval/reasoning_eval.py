from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from common.io import load_jsonl
from common.runtime import choose_device, set_seed
from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.model import GPTConfig, MiniGPT
from stage3_reasoning.self_consistency import (
    choose_consensus,
    extract_final_answer,
    normalize_answer,
    render_candidate_for_verifier,
    sample_candidates,
)
from stage4_verifier.rerank import load_model as load_verifier_model
from stage4_verifier.rerank import rerank_candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="runs/stage2_sft/ckpt.pt")
    parser.add_argument("--data-path", default="datasets/tiny_reasoning/eval.jsonl")
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
    verifier = load_verifier_model(args.verifier_checkpoint, device) if args.verifier_checkpoint else None
    rows = load_jsonl(args.data_path)

    greedy_exact = 0
    consensus_exact = 0
    verifier_exact = 0
    any_match = 0
    greedy_tokens = 0
    sampled_tokens = 0
    verifier_calls = 0

    for index, row in enumerate(rows, start=1):
        expected = row["answer"].strip()
        expected_norm = normalize_answer(expected)
        question = row["question"]

        greedy_candidate = sample_candidates(
            model=model,
            tokenizer=tokenizer,
            question=question,
            num_samples=1,
            max_new_tokens=args.max_new_tokens,
            temperature=0.0,
            top_k=args.top_k,
            device=device,
        )[0]
        sampled_candidates = sample_candidates(
            model=model,
            tokenizer=tokenizer,
            question=question,
            num_samples=args.num_samples,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            device=device,
        )
        consensus = choose_consensus(sampled_candidates)
        verifier_answer = None
        verifier_match = False
        verifier_score = None
        if verifier is not None:
            verifier_model, verifier_tokenizer = verifier
            ranked = rerank_candidates(
                verifier_model,
                verifier_tokenizer,
                f"Question: {question}",
                [render_candidate_for_verifier(candidate) for candidate in sampled_candidates],
                device,
            )
            verifier_calls += len(sampled_candidates)
            verifier_answer = normalize_answer(extract_final_answer(ranked[0].candidate))
            verifier_match = verifier_answer == expected_norm
            verifier_score = ranked[0].score

        greedy_match = greedy_candidate.normalized_answer == expected_norm
        consensus_match = consensus.normalized_answer == expected_norm
        any_candidate_match = any(
            candidate.normalized_answer == expected_norm for candidate in sampled_candidates
        )

        greedy_exact += int(greedy_match)
        consensus_exact += int(consensus_match)
        verifier_exact += int(verifier_match)
        any_match += int(any_candidate_match)
        greedy_tokens += greedy_candidate.generated_tokens
        sampled_tokens += sum(candidate.generated_tokens for candidate in sampled_candidates)

        candidate_answers = ", ".join(
            candidate.final_answer or "[unparsed]" for candidate in sampled_candidates
        )
        print(f"Example {index}")
        print(f"Question: {question}")
        print(f"Expected: {expected}")
        print(
            f"Greedy: {greedy_candidate.final_answer or '[unparsed]'} "
            f"({'match' if greedy_match else 'miss'})"
        )
        print(
            f"Consensus: {consensus.answer} "
            f"(support {consensus.support}/{consensus.total_candidates}, "
            f"{'match' if consensus_match else 'miss'})"
        )
        if verifier is not None:
            print(
                f"Verifier: {ranked[0].candidate} "
                f"(score={verifier_score:.3f}, {'match' if verifier_match else 'miss'})"
            )
        print(f"Candidates: {candidate_answers}")
        print("-" * 72)

    total = max(len(rows), 1)
    print(f"greedy_exact={greedy_exact / total:.3f} ({greedy_exact}/{len(rows)})")
    print(f"self_consistency_exact={consensus_exact / total:.3f} ({consensus_exact}/{len(rows)})")
    if verifier is not None:
        print(f"verifier_rerank_exact={verifier_exact / total:.3f} ({verifier_exact}/{len(rows)})")
    print(f"any_candidate_hit={any_match / total:.3f} ({any_match}/{len(rows)})")
    print(f"avg_greedy_generated_tokens={greedy_tokens / total:.1f}")
    print(f"avg_self_consistency_generated_tokens={sampled_tokens / total:.1f}")
    if verifier is not None:
        print(f"avg_verifier_candidates_scored={verifier_calls / total:.1f}")


if __name__ == "__main__":
    main()
