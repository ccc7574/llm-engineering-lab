from __future__ import annotations

import re
from dataclasses import dataclass

from stage_coding.dataset import CodingTask


@dataclass
class PackedContext:
    files: dict[str, str]
    selected_paths: list[str]
    relevant_recall: float
    context_char_count: int


def tokenize(text: str) -> set[str]:
    raw_tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())
    tokens: set[str] = set()
    for token in raw_tokens:
        if len(token) > 1:
            tokens.add(token)
        for piece in token.split("_"):
            if len(piece) > 1:
                tokens.add(piece)
    return tokens


def build_query_terms(task: CodingTask) -> set[str]:
    terms = set()
    terms |= tokenize(task.instruction)
    terms |= tokenize(task.starter_code)
    terms |= tokenize(task.entry_point)
    return terms


def score_context_file(query_terms: set[str], path: str, content: str) -> tuple[int, int]:
    path_terms = tokenize(path.replace("/", " "))
    content_terms = tokenize(content)
    path_hits = len(query_terms & path_terms)
    content_hits = len(query_terms & content_terms)
    return content_hits, path_hits


def pack_retrieved_context(task: CodingTask, max_files: int = 2) -> PackedContext:
    query_terms = build_query_terms(task)
    ranked = sorted(
        task.context_files.items(),
        key=lambda item: score_context_file(query_terms, item[0], item[1]),
        reverse=True,
    )
    selected = ranked[:max_files]
    selected_paths = [path for path, _ in selected]
    files = {path: content for path, content in selected}

    relevant = set(task.relevant_context_files)
    if relevant:
        relevant_hits = sum(1 for path in selected_paths if path in relevant)
        relevant_recall = relevant_hits / len(relevant)
    else:
        relevant_recall = 0.0

    context_char_count = sum(len(content) for content in files.values())
    return PackedContext(
        files=files,
        selected_paths=selected_paths,
        relevant_recall=relevant_recall,
        context_char_count=context_char_count,
    )
