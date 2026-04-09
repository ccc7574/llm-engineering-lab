from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SFTExample:
    instruction: str
    input: str
    output: str


RESPONSE_MARKER = "### Assistant:\n"


def render_prompt(example: SFTExample) -> str:
    user_input = example.input.strip() if example.input.strip() else "(no additional input)"
    return (
        "### System:\n"
        "You are an internal support assistant. Follow the instruction and respond clearly.\n\n"
        "### Instruction:\n"
        f"{example.instruction.strip()}\n\n"
        "### Input:\n"
        f"{user_input}\n\n"
        f"{RESPONSE_MARKER}"
    )


def render_training_text(example: SFTExample) -> tuple[str, str]:
    prompt = render_prompt(example)
    return prompt, prompt + example.output


def strip_generation(text: str) -> str:
    stripped = text.strip()
    next_turn = stripped.find("\n### ")
    if next_turn != -1:
        stripped = stripped[:next_turn].rstrip()
    return stripped
