"""Массовый тест агентов AURA — реалистичные фразы.

Прогоняет набор типовых команд через orchestrator, показывает кто отвечает.
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROBES = [
    # Elder-care
    "привет", "как дела", "спасибо",
    "аура помоги мне срочно", "я упал не могу встать",
    "напомни выпить таблетки в 20:00", "позвони сыну",
    "проверь мои финансы", "покажи список лекарств",
    "запиши к врачу в 15:00",
    # Система
    "яркость 50", "громкость 30", "обзор", "сколько столов",
    "новый рабочий стол", "какой сегодня день",
    # Медиа
    "включи музыку", "поставь на паузу", "найди видео про космос",
    # Инфо
    "какая погода", "какие новости", "что ты знаешь о кофе",
    # Служебные
    "статус", "проверь ауру", "?" ,
]


async def probe(orch, text: str) -> tuple[str, str, float, str]:
    from aura.core.protocol import AgentRequest
    req = AgentRequest(text=text)
    t0 = time.time()
    try:
        agent = orch.registry.find(req)
        if agent is None:
            return ("NONE", "-", 0.0, "")
        resp = await asyncio.wait_for(agent.handle(req), timeout=5.0)
        dt = (time.time() - t0) * 1000
        return (str(resp.status).split(".")[-1], type(agent).__name__, dt, (resp.text or "")[:70].replace("\n", " "))
    except asyncio.TimeoutError:
        return ("TIMEOUT", type(agent).__name__ if agent else "-", 5000.0, "")
    except Exception as e:
        return ("ERROR", type(agent).__name__ if agent else "-", (time.time()-t0)*1000, f"{type(e).__name__}: {e}"[:60])


async def main() -> int:
    print("=" * 80)
    print("  AURA — Agent Probe (реалистичные фразы)")
    print("=" * 80)
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    print(f"Агентов: {len(orch)}\n")

    stats = {"ok": 0, "error": 0, "timeout": 0, "none": 0, "not_handled": 0}
    errors: list[tuple[str, str, str]] = []
    timeouts: list[tuple[str, str]] = []
    covered: set[str] = set()

    for text in PROBES:
        status, agent, dt, detail = await probe(orch, text)
        stats[status.lower()] = stats.get(status.lower(), 0) + 1
        if agent != "-":
            covered.add(agent)
        icon = {"ok": "✅", "error": "❌", "timeout": "⏱️", "none": "🚫", "not_handled": "⚪"}.get(status.lower(), "?")
        print(f"  {icon} {text:35s} → {agent:30s} {dt:6.0f}ms  {detail}")
        if status == "ERROR":
            errors.append((text, agent, detail))
        elif status == "TIMEOUT":
            timeouts.append((text, agent))

    print("\n" + "=" * 80)
    print("  ИТОГ")
    print("=" * 80)
    for k, v in stats.items():
        print(f"  {k:12s}: {v}")
    print(f"  Уникальных агентов задействовано: {len(covered)}")
    if errors:
        print("\n  ❌ ОШИБКИ:")
        for text, agent, err in errors:
            print(f"    • [{text}] {agent}: {err}")
    if timeouts:
        print("\n  ⏱️  TIMEOUT:")
        for text, agent in timeouts:
            print(f"    • [{text}] {agent}")
    print("=" * 80)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
