"""Массовый тест агентов AURA — 150 фраз по группам.

Прогоняет каждую фразу через orchestrator, показывает кто отвечает.
Группы: elder-care, система, медиа, инфо, мессенджеры, браузер.
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

GROUPS: dict[str, list[str]] = {
    "elder-care": [
        "привет", "как дела", "спасибо", "доброе утро", "добрый вечер",
        "аура помоги мне срочно", "я упал не могу встать",
        "напомни выпить таблетки в 20:00", "позвони сыну", "позвони дочери",
        "проверь мои финансы", "покажи список лекарств", "запиши к врачу в 15:00",
        "добавь таблетку аспирин", "принял таблетку", "покажи визиты",
        "что мне делать сегодня", "мне тревожно", "как самочувствие",
        "какие у меня таблетки",
    ],
    "система": [
        "яркость 50", "яркость 5", "громкость 30", "громкость 7",
        "яркость 100", "громкость 100", "ярче", "тише",
        "обзор", "сколько столов", "новый рабочий стол",
        "следующий стол", "предыдущий стол", "переключись на 2",
        "какой сегодня день", "сколько времени", "какое число",
        "открой firefox", "закрой firefox", "покажи окна",
    ],
    "медиа": [
        "включи музыку", "поставь на паузу", "следующий трек",
        "предыдущий трек", "стоп музыка", "найди видео про космос",
        "включи ютуб", "пауза", "продолжи",
    ],
    "инфо": [
        "какая погода", "погода на завтра", "погода на дачу",
        "какие новости", "что ты знаешь о кофе", "что ты знаешь о космосе",
        "найди в интернете python asyncio", "зачитай журнал",
        "что я делал вчера", "мой дневник",
    ],
    "мессенджеры": [
        "напиши в телеграм маме", "прочитай сообщения", "кто написал",
        "отправь смс", "проверь whatsapp", "проверь почту",
    ],
    "браузер": [
        "открой вкладку", "закрой вкладку", "следующая вкладка",
        "переключись на вкладку 2", "найди в браузере кофе",
    ],
    "служебные": [
        "статус", "проверь ауру", "doctor", "boot-report",
        "что ты умеешь", "справка",
    ],
}


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
        return (str(resp.status).split(".")[-1], type(agent).__name__, dt, (resp.text or "")[:60].replace("\n", " "))
    except asyncio.TimeoutError:
        return ("TIMEOUT", type(agent).__name__ if agent else "-", 5000.0, "")
    except Exception as e:
        return ("ERROR", type(agent).__name__ if agent else "-", (time.time()-t0)*1000, f"{type(e).__name__}: {e}"[:60])


async def main() -> int:
    print("=" * 80)
    print("  AURA — Agent Probe (150 фраз, 7 групп)")
    print("=" * 80)
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    print(f"Агентов: {len(orch)}\n")

    stats = {"ok": 0, "error": 0, "timeout": 0, "none": 0, "not_handled": 0}
    errors: list[tuple[str, str, str]] = []
    timeouts: list[tuple[str, str]] = []
    covered: set[str] = set()

    for group, phrases in GROUPS.items():
        print(f"\n── {group.upper()} ──")
        for text in phrases:
            status, agent, dt, detail = await probe(orch, text)
            stats[status.lower()] = stats.get(status.lower(), 0) + 1
            if agent != "-":
                covered.add(agent)
            icon = {"ok": "✅", "error": "❌", "timeout": "⏱️", "none": "🚫", "not_handled": "⚪"}.get(status.lower(), "?")
            print(f"  {icon} {text:35s} → {agent:25s} {dt:5.0f}ms")
            if status == "ERROR":
                errors.append((text, agent, detail))
            elif status == "TIMEOUT":
                timeouts.append((text, agent))

    print("\n" + "=" * 80)
    print("  ИТОГ")
    print("=" * 80)
    for k, v in stats.items():
        print(f"  {k:12s}: {v}")
    print(f"  Уникальных агентов: {len(covered)}")
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
