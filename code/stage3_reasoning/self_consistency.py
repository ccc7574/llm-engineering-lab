from __future__ import annotations

import re
from dataclasses import dataclass

import torch

from common.tokenizer import CharTokenizer
from stage1_nanogpt_core.model import MiniGPT
from stage2_sft.dataset import REASONING_INSTRUCTION
from stage2_sft.prompt_template import SFTExample, render_prompt, strip_generation

FINAL_ANSWER_PATTERNS = (
    re.compile(r"final answer\s*:\s*(.+)", re.IGNORECASE),
    re.compile(r"answer\s*:\s*(.+)", re.IGNORECASE),
)
TIME_PATTERN = re.compile(r"\b\d{1,2}:\d{2}\b")
NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass
class ReasoningCandidate:
    text: str
    final_answer: str
    normalized_answer: str
    generated_tokens: int


@dataclass
class ConsensusResult:
    answer: str
    normalized_answer: str
    support: int
    total_candidates: int
    representative_text: str
    answer_counts: dict[str, int]


def build_reasoning_prompt(question: str) -> str:
    return render_prompt(
        SFTExample(
            instruction=REASONING_INSTRUCTION,
            input=question.strip(),
            output="",
        )
    )


def normalize_answer(text: str) -> str:
    lowered = text.strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip(" .,:;!?\"'")


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


def extract_final_answer(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    for line in reversed([line.strip() for line in stripped.splitlines() if line.strip()]):
        for pattern in FINAL_ANSWER_PATTERNS:
            match = pattern.search(line)
            if match:
                return match.group(1).strip().strip(" .")
        time_matches = TIME_PATTERN.findall(line)
        if time_matches:
            return time_matches[-1]
        number_matches = NUMBER_PATTERN.findall(line)
        if number_matches:
            return number_matches[-1]

    time_matches = TIME_PATTERN.findall(stripped)
    if time_matches:
        return time_matches[-1]
    number_matches = NUMBER_PATTERN.findall(stripped)
    if number_matches:
        return number_matches[-1]
    return stripped.splitlines()[-1].strip()


def render_candidate_for_verifier(candidate: ReasoningCandidate) -> str:
    text = candidate.text.strip()
    if any(pattern.search(text) for pattern in FINAL_ANSWER_PATTERNS):
        return text
    if candidate.final_answer:
        if text:
            return f"{text}\nFinal Answer: {candidate.final_answer}"
        return f"Final Answer: {candidate.final_answer}"
    return text


@torch.no_grad()
def generate_candidate(
    model: MiniGPT,
    tokenizer: CharTokenizer,
    question: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    device: str,
) -> ReasoningCandidate:
    prompt = build_reasoning_prompt(question)
    prompt_ids = tokenizer.encode(make_tokenizer_compatible(prompt, tokenizer))
    prompt_tensor = torch.tensor(
        [prompt_ids[-model.config.block_size :]],
        dtype=torch.long,
        device=device,
    )
    generated = model.generate(
        prompt_tensor,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
    )[0].tolist()
    completion_ids = generated[len(prompt_tensor[0]) :]
    completion_text = strip_generation(tokenizer.decode(completion_ids))
    final_answer = extract_final_answer(completion_text)
    return ReasoningCandidate(
        text=completion_text,
        final_answer=final_answer,
        normalized_answer=normalize_answer(final_answer),
        generated_tokens=len(completion_ids),
    )


def sample_candidates(
    model: MiniGPT,
    tokenizer: CharTokenizer,
    question: str,
    num_samples: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    device: str,
) -> list[ReasoningCandidate]:
    if num_samples <= 0:
        raise ValueError("num_samples must be positive")
    return [
        generate_candidate(
            model=model,
            tokenizer=tokenizer,
            question=question,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            device=device,
        )
        for _ in range(num_samples)
    ]


def choose_consensus(candidates: list[ReasoningCandidate]) -> ConsensusResult:
    if not candidates:
        raise ValueError("at least one candidate is required")

    answer_counts: dict[str, int] = {}
    representative_by_answer: dict[str, ReasoningCandidate] = {}
    raw_fallback = "__raw__"
    for candidate in candidates:
        key = candidate.normalized_answer or normalize_answer(candidate.text) or raw_fallback
        answer_counts[key] = answer_counts.get(key, 0) + 1
        representative_by_answer.setdefault(key, candidate)

    best_key, best_count = max(
        answer_counts.items(),
        key=lambda item: (item[1], -representative_by_answer[item[0]].generated_tokens),
    )
    representative = representative_by_answer[best_key]
    return ConsensusResult(
        answer=representative.final_answer or representative.text.strip(),
        normalized_answer=best_key,
        support=best_count,
        total_candidates=len(candidates),
        representative_text=representative.text,
        answer_counts=answer_counts,
    )
