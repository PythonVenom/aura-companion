"""Agent Watchdog — проверка живости агентов.

Наука: Watchdog Timer (embedded), Circuit Breaker (Nygard 2007).
Раз в N сек — ping агентов, лог в receipts.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class AgentHealth:
    name: str
    alive: bool = True
    last_ping: float = 0.0
    failures: int = 0


@dataclass
class WatchdogReport:
    total: int = 0
    alive: int = 0
    dead: list[str] = field(default_factory=list)
    ts: float = 0.0


def check_all() -> WatchdogReport:
    """Проверить всех агентов через can_handle."""
    try:
        from aura.bootstrap import build_orchestrator
        from aura.core.protocol import AgentRequest
        orch = build_orchestrator()
    except Exception:
        return WatchdogReport(ts=time.time())

    rep = WatchdogReport(ts=time.time())
    probe = AgentRequest(text="аура тест")
    for a in orch.registry._agents:
        rep.total += 1
        try:
            a.can_handle(probe)
            rep.alive += 1
        except Exception:
            rep.dead.append(type(a).__name__)
    return rep


def to_text() -> str:
    r = check_all()
    lines = [f"🐕 Watchdog: {r.alive}/{r.total} живы"]
    if r.dead:
        for name in r.dead[:10]:
            lines.append(f"  ❌ {name}")
    return "\n".join(lines)


def main() -> None:
    print(to_text())


if __name__ == "__main__":
    main()


__all__ = ["AgentHealth", "WatchdogReport", "check_all", "main", "to_text"]
