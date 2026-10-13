"""Aura Agent Contract — контракт на века."""
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Event:
    topic: str
    payload: dict[str, Any]
    version: int = 1
    src: str = ""
    ts: float = 0.0


@dataclass
class AgentContext:
    bus: Any
    capabilities: list
    log: Any
    config: dict[str, Any] = field(default_factory=dict)


class AgentBehaviour(Protocol):
    name: str
    version: str

    async def start(self, ctx: AgentContext) -> None: ...
    async def handle(self, event: Event) -> None: ...
    async def health(self) -> dict[str, Any]: ...
    async def stop(self) -> None: ...
