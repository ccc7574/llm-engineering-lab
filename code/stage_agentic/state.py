from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentState:
    memory: dict[str, str] = field(default_factory=dict)
    observations: list[str] = field(default_factory=list)
    state_reads: int = 0
    state_writes: int = 0
    recovery_attempts: int = 0

    def observe(self, message: str) -> None:
        self.observations.append(message)

    def store(self, key: str, value: str) -> None:
        self.memory[key] = str(value)
        self.state_writes += 1
        self.observe(f"state.store({key}) -> {value}")

    def recall(self, key: str) -> str:
        self.state_reads += 1
        value = self.memory[key]
        self.observe(f"state.recall({key}) -> {value}")
        return value

    def mark_recovery(self, reason: str) -> None:
        self.recovery_attempts += 1
        self.observe(f"recovery -> {reason}")
