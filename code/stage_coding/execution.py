from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    passed: bool
    failure_type: str | None
    failure_message: str | None


def build_context_prelude(context_files: dict[str, str]) -> str:
    parts = []
    for path, content in context_files.items():
        parts.append(f"# file: {path}\n{content.strip()}")
    return "\n\n".join(parts)


def evaluate_python_patch(
    repo_files: dict[str, str],
    patch_files: dict[str, str],
    tests: list[str],
    execution_order: list[str],
) -> ExecutionResult:
    namespace: dict[str, object] = {}
    merged_files = dict(repo_files)
    merged_files.update(patch_files)

    for path in execution_order:
        source = merged_files[path]
        try:
            ast.parse(source)
        except SyntaxError as exc:
            return ExecutionResult(False, "syntax_error", f"{path} | {exc}")
        try:
            exec(source, namespace, namespace)
        except Exception as exc:  # noqa: BLE001
            return ExecutionResult(False, "runtime_error", f"{path} | {exc}")

    for test in tests:
        try:
            exec(test, namespace, namespace)
        except AssertionError:
            return ExecutionResult(False, "assertion_failed", test)
        except Exception as exc:  # noqa: BLE001
            return ExecutionResult(False, "test_runtime_error", f"{test} | {exc}")

    return ExecutionResult(True, None, None)


def evaluate_python_candidate(
    candidate: str,
    tests: list[str],
    prelude: str = "",
) -> ExecutionResult:
    try:
        ast.parse(candidate)
    except SyntaxError as exc:
        return ExecutionResult(False, "syntax_error", str(exc))

    namespace: dict[str, object] = {}
    if prelude.strip():
        try:
            exec(prelude, namespace, namespace)
        except Exception as exc:  # noqa: BLE001
            return ExecutionResult(False, "context_runtime_error", str(exc))

    try:
        exec(candidate, namespace, namespace)
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult(False, "runtime_error", str(exc))

    for test in tests:
        try:
            exec(test, namespace, namespace)
        except AssertionError:
            return ExecutionResult(False, "assertion_failed", test)
        except Exception as exc:  # noqa: BLE001
            return ExecutionResult(False, "test_runtime_error", f"{test} | {exc}")

    return ExecutionResult(True, None, None)
