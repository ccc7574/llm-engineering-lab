from __future__ import annotations

import re

import torch

TIME_PATTERN = re.compile(r"\b(\d{1,2}):(\d{2})\b")
NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")
FINAL_ANSWER_PATTERN = re.compile(r"final answer\s*:\s*(.+)", re.IGNORECASE)


def extract_final_answer_text(candidate: str) -> str:
    stripped = candidate.strip()
    if not stripped:
        return ""
    for line in reversed([line.strip() for line in stripped.splitlines() if line.strip()]):
        match = FINAL_ANSWER_PATTERN.search(line)
        if match:
            return match.group(1).strip()
    return stripped.splitlines()[-1].strip()


def parse_time_value(text: str) -> int | None:
    match = TIME_PATTERN.search(text)
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2))
    return hours * 60 + minutes


def parse_number_value(text: str) -> float | None:
    match = NUMBER_PATTERN.search(text)
    if not match:
        return None
    return float(match.group(0))


def parse_candidate_answer(candidate: str) -> tuple[float | int | None, str]:
    final_text = extract_final_answer_text(candidate)
    parsed_time = parse_time_value(final_text)
    if parsed_time is not None:
        return parsed_time, "time"
    parsed_number = parse_number_value(final_text)
    if parsed_number is not None:
        return parsed_number, "number"
    return None, "unknown"


def infer_expected_answer(prompt: str) -> tuple[float | int | None, str]:
    text = prompt.strip()

    time_start_match = re.search(r"at\s+(\d{1,2}:\d{2}).*?(\d+)\s+minutes later", text, re.IGNORECASE)
    if time_start_match:
        base_minutes = parse_time_value(time_start_match.group(1))
        delta = int(time_start_match.group(2))
        if base_minutes is not None:
            return base_minutes + delta, "time"

    every_match = re.search(r"every\s+(\d+)\s+minutes.*?(?:in|one)\s+(\d+)\s+minutes", text, re.IGNORECASE)
    if every_match:
        interval = int(every_match.group(1))
        total = int(every_match.group(2))
        if interval != 0:
            return total / interval, "number"
    if re.search(r"every\s+(\d+)\s+minutes", text, re.IGNORECASE) and re.search(r"one hour", text, re.IGNORECASE):
        interval = int(re.search(r"every\s+(\d+)\s+minutes", text, re.IGNORECASE).group(1))
        if interval != 0:
            return 60 / interval, "number"

    numbers = [float(match) for match in NUMBER_PATTERN.findall(text)]
    lowered = text.lower()
    if len(numbers) >= 2:
        a = numbers[0]
        b = numbers[1]
        if any(keyword in lowered for keyword in ("each", "every")) and any(
            keyword in lowered for keyword in ("total", "all checks", "minutes for all", "minutes total")
        ):
            return a * b, "number"
        if any(keyword in lowered for keyword in ("remain", "left")) and any(
            keyword in lowered for keyword in ("finish", "processed", "more")
        ):
            return a - b if len(numbers) == 2 else a - b - numbers[2], "number"
        if any(keyword in lowered for keyword in ("total", "in total", "how many widgets", "how long")):
            return a + b, "number"

    if len(numbers) >= 3 and any(keyword in lowered for keyword in ("remain", "left")):
        return numbers[0] - numbers[1] - numbers[2], "number"

    return None, "unknown"


def build_numeric_features(prompt: str, candidate: str) -> torch.Tensor:
    expected, expected_type = infer_expected_answer(prompt)
    candidate_value, candidate_type = parse_candidate_answer(candidate)
    has_final_answer = 1.0 if FINAL_ANSWER_PATTERN.search(candidate) else 0.0
    prompt_parseable = 1.0 if expected is not None else 0.0
    candidate_parseable = 1.0 if candidate_value is not None else 0.0
    same_type = 1.0 if expected_type == candidate_type and expected_type != "unknown" else 0.0
    exact_match = 0.0
    closeness = 0.0

    if expected is not None and candidate_value is not None and expected_type == candidate_type:
        if expected_type == "time":
            exact_match = 1.0 if int(expected) == int(candidate_value) else 0.0
            closeness = exact_match
        else:
            diff = abs(float(expected) - float(candidate_value))
            exact_match = 1.0 if diff < 1e-6 else 0.0
            closeness = 1.0 / (1.0 + diff)

    normalized_length = min(len(candidate.strip()) / 120.0, 1.0)
    return torch.tensor(
        [
            prompt_parseable,
            candidate_parseable,
            has_final_answer,
            same_type,
            exact_match,
            closeness * normalized_length,
        ],
        dtype=torch.float32,
    )
