from __future__ import annotations

from stage_coding.dataset import CodingTask


def render_prompt(task: CodingTask, context_files: dict[str, str] | None = None) -> str:
    context_block = ""
    files = task.context_files if context_files is None else context_files
    if files:
        rendered_context = []
        for path, content in files.items():
            rendered_context.append(f"[{path}]\n{content.rstrip()}")
        context_block = "### Repository Context:\n" + "\n\n".join(rendered_context) + "\n\n"
    return (
        "### System:\n"
        "You are a coding assistant. Complete the function so it passes the hidden tests.\n\n"
        "### Instruction:\n"
        f"{task.instruction.strip()}\n\n"
        f"{context_block}"
        "### Starter Code:\n"
        f"{task.starter_code.rstrip()}\n\n"
        "### Assistant:\n"
    )
