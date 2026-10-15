"""Agent Debug Dashboard — per-agent health (CLI).

Наука: Observability (SRE Book). Быстрый дебаг 118 агентов.
"""
from __future__ import annotations

import time

from aura.core.protocol import AgentRequest


def scan() -> list[dict]:
    """Сканировать всех агентов."""
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    probe = AgentRequest(text="аура тест")
    rows = []
    for a in orch.registry._agents:
        name = type(a).__name__
        t0 = time.perf_counter()
        try:
            can = a.can_handle(probe)
            dt = (time.perf_counter() - t0) * 1000
            rows.append({
                "name": name,
                "can_handle": can,
                "ms": round(dt, 2),
                "ok": True,
            })
        except Exception as e:
            rows.append({
                "name": name,
                "can_handle": False,
                "ms": 0.0,
                "ok": False,
                "error": str(e)[:50],
            })
    return rows


def report(sort_by: str = "ms") -> str:
    rows = scan()
    if sort_by == "ms":
        rows.sort(key=lambda r: -r["ms"])
    else:
        rows.sort(key=lambda r: r["name"])
    total = len(rows)
    errs = sum(1 for r in rows if not r["ok"])
    handles = sum(1 for r in rows if r["can_handle"])
    lines = [f"🔬 Debug Dashboard: {total} агентов "
             f"(OK: {total - errs}, ERR: {errs}, CAN: {handles})"]
    lines.append(f"{'─' * 60}")
    for r in rows[:20]:
        icon = "✅" if r["ok"] else "❌"
        can = "🎯" if r["can_handle"] else "  "
        lines.append(f"  {icon}{can} {r['name']:35s} {r['ms']:>7.2f} ms")
    return "\n".join(lines)


def main() -> None:
    print(report())


if __name__ == "__main__":
    main()


__all__ = ["main", "report", "scan"]
