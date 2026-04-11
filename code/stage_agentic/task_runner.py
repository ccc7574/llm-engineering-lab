from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.runtime import ensure_dir
from stage_agentic.dataset import AgentTask, load_agent_tasks
from stage_agentic.state import AgentState
from stage_agentic.tools import (
    is_escalation_channel,
    lookup_backup_channel,
    lookup_primary_channel,
    lookup_retry_multiplier,
    lookup_service_owner,
    lookup_service_tier,
    multiply,
    normalize_channel,
)


@dataclass
class AgentRun:
    task_id: str
    strategy: str
    answer: str
    tool_calls: int
    steps: int
    trace: list[str]
    state_reads: int = 0
    state_writes: int = 0
    recovery_attempts: int = 0
    reflection_steps: int = 0
    plan_steps: int = 0
    observer_checks: int = 0
    final_state: dict[str, str] | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default="datasets/tiny_agentic/eval.jsonl")
    parser.add_argument("--task-id", default=None)
    parser.add_argument(
        "--strategy",
        choices=["direct", "tool_use", "stateful", "reflective", "planner_observer", "reference"],
        default="tool_use",
    )
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def direct_answer(task: AgentTask) -> str:
    guesses = {
        "incident_total_minutes": "15",
        "escalation_channel_check": "false",
        "owner_message": "Notify ops in sev ops",
        "owner_channel_memory": "Page payments via payments",
        "fallback_recovery_message": "Notify search-oncall in search-hotline",
        "reflection_retry_plan": "15",
        "reflection_channel_repair": "Notify search-oncall in search-hotline",
        "planner_safe_escalation_message": "Notify search-oncall in search-hotline",
        "planner_threshold_dispatch": "Page auth-oncall in auth-bridge after 30 minutes",
    }
    return guesses.get(task.task_id, "")


def tool_use_answer(task: AgentTask) -> AgentRun:
    trace: list[str] = []
    tool_calls = 0

    if task.task_id == "incident_total_minutes":
        tier = lookup_service_tier("auth", task.tool_context)
        trace.append(f"lookup_service_tier(auth) -> {tier}")
        tool_calls += 1
        multiplier = lookup_retry_multiplier(tier, task.tool_context)
        trace.append(f"lookup_retry_multiplier({tier}) -> {multiplier}")
        tool_calls += 1
        total = multiply(5 * 3, multiplier)
        trace.append(f"multiply(15, {multiplier}) -> {total}")
        tool_calls += 1
        answer = str(total)
    elif task.task_id == "escalation_channel_check":
        channel = normalize_channel(" SEV Payments ")
        trace.append(f"normalize_channel(' SEV Payments ') -> {channel}")
        tool_calls += 1
        verdict = is_escalation_channel(channel, task.tool_context)
        trace.append(f"is_escalation_channel({channel}) -> {verdict}")
        tool_calls += 1
        answer = str(verdict).lower()
    elif task.task_id == "owner_message":
        owner = lookup_service_owner("search", task.tool_context)
        trace.append(f"lookup_service_owner(search) -> {owner}")
        tool_calls += 1
        channel = normalize_channel("Sev Ops")
        trace.append(f"normalize_channel('Sev Ops') -> {channel}")
        tool_calls += 1
        answer = f"Notify {owner} in {channel}"
    elif task.task_id == "owner_channel_memory":
        latest_value = lookup_service_owner("payments", task.tool_context)
        trace.append(f"lookup_service_owner(payments) -> {latest_value}")
        tool_calls += 1
        latest_value = normalize_channel(" SEV Payments ")
        trace.append(f"normalize_channel(' SEV Payments ') -> {latest_value}")
        tool_calls += 1
        answer = f"Page {latest_value} via {latest_value}"
    elif task.task_id == "fallback_recovery_message":
        owner = lookup_service_owner("search", task.tool_context)
        trace.append(f"lookup_service_owner(search) -> {owner}")
        tool_calls += 1
        channel = normalize_channel(" Search Hotline ")
        trace.append(f"normalize_channel(' Search Hotline ') -> {channel}")
        tool_calls += 1
        verdict = is_escalation_channel(channel, task.tool_context)
        trace.append(f"is_escalation_channel({channel}) -> {verdict}")
        tool_calls += 1
        answer = f"Notify {owner} in {channel}"
    elif task.task_id == "reflection_retry_plan":
        total = multiply(5, 3)
        trace.append(f"multiply(5, 3) -> {total}")
        tool_calls += 1
        answer = str(total)
    elif task.task_id == "reflection_channel_repair":
        owner = lookup_service_owner("search", task.tool_context)
        trace.append(f"lookup_service_owner(search) -> {owner}")
        tool_calls += 1
        channel = normalize_channel(" Search Hotline ")
        trace.append(f"normalize_channel(' Search Hotline ') -> {channel}")
        tool_calls += 1
        answer = f"Notify {owner} in {channel}"
    else:
        answer = ""

    return AgentRun(
        task_id=task.task_id,
        strategy="tool_use",
        answer=answer,
        tool_calls=tool_calls,
        steps=len(trace),
        trace=trace,
    )


def stateful_answer(task: AgentTask) -> AgentRun:
    state = AgentState()
    trace: list[str] = []
    tool_calls = 0

    if task.task_id == "incident_total_minutes":
        tier = lookup_service_tier("auth", task.tool_context)
        trace.append(f"lookup_service_tier(auth) -> {tier}")
        tool_calls += 1
        state.store("service_tier", tier)
        multiplier = lookup_retry_multiplier(state.recall("service_tier"), task.tool_context)
        trace.append(f"lookup_retry_multiplier({tier}) -> {multiplier}")
        tool_calls += 1
        state.store("retry_multiplier", str(multiplier))
        total = multiply(5 * 3, int(state.recall("retry_multiplier")))
        trace.append(f"multiply(15, {multiplier}) -> {total}")
        tool_calls += 1
        answer = str(total)
    elif task.task_id == "escalation_channel_check":
        channel = normalize_channel(" SEV Payments ")
        trace.append(f"normalize_channel(' SEV Payments ') -> {channel}")
        tool_calls += 1
        state.store("channel", channel)
        verdict = is_escalation_channel(state.recall("channel"), task.tool_context)
        trace.append(f"is_escalation_channel({channel}) -> {verdict}")
        tool_calls += 1
        answer = str(verdict).lower()
    elif task.task_id == "owner_message":
        owner = lookup_service_owner("search", task.tool_context)
        trace.append(f"lookup_service_owner(search) -> {owner}")
        tool_calls += 1
        state.store("owner", owner)
        channel = normalize_channel("Sev Ops")
        trace.append(f"normalize_channel('Sev Ops') -> {channel}")
        tool_calls += 1
        state.store("channel", channel)
        answer = f"Notify {state.recall('owner')} in {state.recall('channel')}"
    elif task.task_id == "owner_channel_memory":
        owner = lookup_service_owner("payments", task.tool_context)
        trace.append(f"lookup_service_owner(payments) -> {owner}")
        tool_calls += 1
        state.store("owner", owner)
        channel = normalize_channel(" SEV Payments ")
        trace.append(f"normalize_channel(' SEV Payments ') -> {channel}")
        tool_calls += 1
        state.store("channel", channel)
        answer = f"Page {state.recall('owner')} via {state.recall('channel')}"
    elif task.task_id == "fallback_recovery_message":
        owner = lookup_service_owner("search", task.tool_context)
        trace.append(f"lookup_service_owner(search) -> {owner}")
        tool_calls += 1
        state.store("owner", owner)
        channel = normalize_channel(" Search Hotline ")
        trace.append(f"normalize_channel(' Search Hotline ') -> {channel}")
        tool_calls += 1
        state.store("channel", channel)
        verdict = is_escalation_channel(state.recall("channel"), task.tool_context)
        trace.append(f"is_escalation_channel({channel}) -> {verdict}")
        tool_calls += 1
        if not verdict:
            state.mark_recovery("fallback to sev-ops")
            channel = normalize_channel("Sev Ops")
            trace.append(f"normalize_channel('Sev Ops') -> {channel}")
            tool_calls += 1
            state.store("channel", channel)
        answer = f"Notify {state.recall('owner')} in {state.recall('channel')}"
    elif task.task_id == "planner_safe_escalation_message":
        owner = lookup_service_owner("search", task.tool_context)
        trace.append(f"lookup_service_owner(search) -> {owner}")
        tool_calls += 1
        state.store("owner", owner)
        primary_channel = lookup_primary_channel("search", task.tool_context)
        trace.append(f"lookup_primary_channel(search) -> {primary_channel}")
        tool_calls += 1
        channel = normalize_channel(primary_channel)
        trace.append(f"normalize_channel({primary_channel!r}) -> {channel}")
        tool_calls += 1
        state.store("channel", channel)
        answer = f"Notify {state.recall('owner')} in {state.recall('channel')}"
    elif task.task_id == "planner_threshold_dispatch":
        tier = lookup_service_tier("auth", task.tool_context)
        trace.append(f"lookup_service_tier(auth) -> {tier}")
        tool_calls += 1
        state.store("service_tier", tier)
        multiplier = lookup_retry_multiplier(state.recall("service_tier"), task.tool_context)
        trace.append(f"lookup_retry_multiplier({tier}) -> {multiplier}")
        tool_calls += 1
        state.store("retry_multiplier", str(multiplier))
        base_wait = int(task.tool_context["base_wait_minutes"])
        retries = int(task.tool_context["retries"])
        total = multiply(base_wait * retries, int(state.recall("retry_multiplier")))
        trace.append(f"multiply({base_wait * retries}, {multiplier}) -> {total}")
        tool_calls += 1
        state.store("total_wait_minutes", str(total))
        owner = lookup_service_owner("auth", task.tool_context)
        trace.append(f"lookup_service_owner(auth) -> {owner}")
        tool_calls += 1
        state.store("owner", owner)
        primary_channel = lookup_primary_channel("auth", task.tool_context)
        trace.append(f"lookup_primary_channel(auth) -> {primary_channel}")
        tool_calls += 1
        channel = normalize_channel(primary_channel)
        trace.append(f"normalize_channel({primary_channel!r}) -> {channel}")
        tool_calls += 1
        state.store("channel", channel)
        threshold = int(task.tool_context["page_threshold_minutes"])
        action = "Page" if total >= threshold else "Notify"
        answer = (
            f"{action} {state.recall('owner')} in {state.recall('channel')} "
            f"after {state.recall('total_wait_minutes')} minutes"
        )
    else:
        answer = ""

    trace.extend(state.observations)
    return AgentRun(
        task_id=task.task_id,
        strategy="stateful",
        answer=answer,
        tool_calls=tool_calls,
        steps=len(trace),
        trace=trace,
        state_reads=state.state_reads,
        state_writes=state.state_writes,
        recovery_attempts=state.recovery_attempts,
        final_state=dict(state.memory),
    )


def reflective_answer(task: AgentTask) -> AgentRun:
    state = AgentState()
    trace: list[str] = []
    tool_calls = 0
    reflection_steps = 0

    if task.task_id == "reflection_retry_plan":
        draft_total = multiply(5, 3)
        trace.append(f"draft.multiply(5, 3) -> {draft_total}")
        tool_calls += 1
        state.store("draft_total", str(draft_total))
        tier = lookup_service_tier("auth", task.tool_context)
        trace.append(f"lookup_service_tier(auth) -> {tier}")
        tool_calls += 1
        multiplier = lookup_retry_multiplier(tier, task.tool_context)
        trace.append(f"lookup_retry_multiplier({tier}) -> {multiplier}")
        tool_calls += 1
        reflection_steps += 1
        trace.append("reflection.check_multiplier -> draft missing retry multiplier")
        repaired_total = multiply(int(state.recall("draft_total")), multiplier)
        trace.append(f"revise.multiply({state.recall('draft_total')}, {multiplier}) -> {repaired_total}")
        tool_calls += 1
        answer = str(repaired_total)
    elif task.task_id == "reflection_channel_repair":
        owner = lookup_service_owner("search", task.tool_context)
        trace.append(f"lookup_service_owner(search) -> {owner}")
        tool_calls += 1
        state.store("owner", owner)
        channel = normalize_channel(" Search Hotline ")
        trace.append(f"normalize_channel(' Search Hotline ') -> {channel}")
        tool_calls += 1
        state.store("channel", channel)
        verdict = is_escalation_channel(state.recall("channel"), task.tool_context)
        trace.append(f"is_escalation_channel({channel}) -> {verdict}")
        tool_calls += 1
        if not verdict:
            reflection_steps += 1
            trace.append("reflection.check_channel -> draft channel is not escalation-safe")
            repaired_channel = normalize_channel("Sev Ops")
            trace.append(f"normalize_channel('Sev Ops') -> {repaired_channel}")
            tool_calls += 1
            state.store("channel", repaired_channel)
        answer = f"Notify {state.recall('owner')} in {state.recall('channel')}"
    else:
        return stateful_answer(task)

    trace.extend(state.observations)
    return AgentRun(
        task_id=task.task_id,
        strategy="reflective",
        answer=answer,
        tool_calls=tool_calls,
        steps=len(trace),
        trace=trace,
        state_reads=state.state_reads,
        state_writes=state.state_writes,
        recovery_attempts=state.recovery_attempts,
        reflection_steps=reflection_steps,
        final_state=dict(state.memory),
    )


def planner_observer_answer(task: AgentTask) -> AgentRun:
    state = AgentState()
    trace: list[str] = []
    tool_calls = 0
    plan_steps = 0
    observer_checks = 0

    if task.task_id == "planner_safe_escalation_message":
        plan = [
            "lookup service owner",
            "read and normalize the primary dispatch channel",
            "audit the draft channel against escalation policy",
            "reroute to the backup escalation channel if needed",
            "compose the final notification",
        ]
        plan_steps = len(plan)
        trace.extend(f"planner.step_{index} -> {step}" for index, step in enumerate(plan, start=1))

        owner = lookup_service_owner("search", task.tool_context)
        trace.append(f"lookup_service_owner(search) -> {owner}")
        tool_calls += 1
        state.store("owner", owner)
        primary_channel = lookup_primary_channel("search", task.tool_context)
        trace.append(f"lookup_primary_channel(search) -> {primary_channel}")
        tool_calls += 1
        normalized_channel = normalize_channel(primary_channel)
        trace.append(f"normalize_channel({primary_channel!r}) -> {normalized_channel}")
        tool_calls += 1
        state.store("channel", normalized_channel)

        draft_channel = state.recall("channel")
        primary_safe = is_escalation_channel(draft_channel, task.tool_context)
        trace.append(f"observer.check_dispatch_channel({draft_channel}) -> {primary_safe}")
        tool_calls += 1
        observer_checks += 1
        if not primary_safe:
            state.mark_recovery("observer reroute to escalation-safe backup channel")
            backup_channel = lookup_backup_channel("search", task.tool_context)
            trace.append(f"lookup_backup_channel(search) -> {backup_channel}")
            tool_calls += 1
            normalized_backup = normalize_channel(backup_channel)
            trace.append(f"normalize_channel({backup_channel!r}) -> {normalized_backup}")
            tool_calls += 1
            state.store("channel", normalized_backup)

        final_channel = state.recall("channel")
        final_safe = is_escalation_channel(final_channel, task.tool_context)
        trace.append(f"observer.check_final_channel({final_channel}) -> {final_safe}")
        tool_calls += 1
        observer_checks += 1
        answer = f"Notify {state.recall('owner')} in {final_channel}"
    elif task.task_id == "planner_threshold_dispatch":
        plan = [
            "lookup service tier",
            "lookup retry multiplier and compute total wait",
            "decide whether the incident crosses the paging threshold",
            "lookup the owner and primary dispatch channel",
            "audit the dispatch channel for escalation safety",
            "emit the final paging command",
        ]
        plan_steps = len(plan)
        trace.extend(f"planner.step_{index} -> {step}" for index, step in enumerate(plan, start=1))

        tier = lookup_service_tier("auth", task.tool_context)
        trace.append(f"lookup_service_tier(auth) -> {tier}")
        tool_calls += 1
        state.store("service_tier", tier)
        multiplier = lookup_retry_multiplier(state.recall("service_tier"), task.tool_context)
        trace.append(f"lookup_retry_multiplier({tier}) -> {multiplier}")
        tool_calls += 1
        state.store("retry_multiplier", str(multiplier))

        base_wait = int(task.tool_context["base_wait_minutes"])
        retries = int(task.tool_context["retries"])
        total = multiply(base_wait * retries, int(state.recall("retry_multiplier")))
        trace.append(f"multiply({base_wait * retries}, {multiplier}) -> {total}")
        tool_calls += 1
        state.store("total_wait_minutes", str(total))

        threshold = int(task.tool_context["page_threshold_minutes"])
        page_required = total >= threshold
        trace.append(f"observer.check_page_threshold({total} >= {threshold}) -> {page_required}")
        observer_checks += 1

        owner = lookup_service_owner("auth", task.tool_context)
        trace.append(f"lookup_service_owner(auth) -> {owner}")
        tool_calls += 1
        state.store("owner", owner)
        primary_channel = lookup_primary_channel("auth", task.tool_context)
        trace.append(f"lookup_primary_channel(auth) -> {primary_channel}")
        tool_calls += 1
        normalized_channel = normalize_channel(primary_channel)
        trace.append(f"normalize_channel({primary_channel!r}) -> {normalized_channel}")
        tool_calls += 1
        state.store("channel", normalized_channel)

        draft_channel = state.recall("channel")
        channel_safe = is_escalation_channel(draft_channel, task.tool_context)
        trace.append(f"observer.check_dispatch_channel({draft_channel}) -> {channel_safe}")
        tool_calls += 1
        observer_checks += 1
        if not channel_safe:
            state.mark_recovery("observer reroute to escalation-safe backup channel")
            backup_channel = lookup_backup_channel("auth", task.tool_context)
            trace.append(f"lookup_backup_channel(auth) -> {backup_channel}")
            tool_calls += 1
            normalized_backup = normalize_channel(backup_channel)
            trace.append(f"normalize_channel({backup_channel!r}) -> {normalized_backup}")
            tool_calls += 1
            state.store("channel", normalized_backup)

        action = "Page" if page_required else "Notify"
        answer = (
            f"{action} {state.recall('owner')} in {state.recall('channel')} "
            f"after {state.recall('total_wait_minutes')} minutes"
        )
    else:
        return reflective_answer(task)

    trace.extend(state.observations)
    return AgentRun(
        task_id=task.task_id,
        strategy="planner_observer",
        answer=answer,
        tool_calls=tool_calls,
        steps=len(trace),
        trace=trace,
        state_reads=state.state_reads,
        state_writes=state.state_writes,
        recovery_attempts=state.recovery_attempts,
        plan_steps=plan_steps,
        observer_checks=observer_checks,
        final_state=dict(state.memory),
    )


def build_run(task: AgentTask, strategy: str) -> AgentRun:
    if strategy == "reference":
        return AgentRun(
            task_id=task.task_id,
            strategy=strategy,
            answer=task.expected_answer,
            tool_calls=0,
            steps=0,
            trace=["reference answer"],
        )
    if strategy == "stateful":
        return stateful_answer(task)
    if strategy == "reflective":
        return reflective_answer(task)
    if strategy == "planner_observer":
        return planner_observer_answer(task)
    if strategy == "tool_use":
        return tool_use_answer(task)
    answer = direct_answer(task)
    return AgentRun(
        task_id=task.task_id,
        strategy=strategy,
        answer=answer,
        tool_calls=0,
        steps=1,
        trace=[f"direct_guess -> {answer}"],
    )


def main() -> None:
    args = parse_args()
    tasks = load_agent_tasks(args.data_path)
    if args.task_id:
        tasks = [task for task in tasks if task.task_id == args.task_id]

    rows = []
    for task in tasks:
        run = build_run(task, args.strategy)
        print(f"Task: {task.task_id}")
        print(f"Answer: {run.answer}")
        print(f"Tool calls: {run.tool_calls}")
        print(f"State reads/writes: {run.state_reads}/{run.state_writes}")
        print(f"Recovery attempts: {run.recovery_attempts}")
        print(f"Reflection/planning/observer: {run.reflection_steps}/{run.plan_steps}/{run.observer_checks}")
        for step in run.trace:
            print(f"  {step}")
        if run.final_state:
            print(f"Final state: {json.dumps(run.final_state, ensure_ascii=False)}")
        print("-" * 72)
        rows.append(asdict(run))

    if args.output:
        output_path = Path(args.output)
        ensure_dir(output_path.parent)
        output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"saved agent runs to {output_path}")


if __name__ == "__main__":
    main()
