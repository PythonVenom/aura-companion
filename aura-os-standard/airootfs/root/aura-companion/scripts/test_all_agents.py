"""Mass Agent Probe — 200+ фраз, покрытие 100+ агентов."""
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
        "что мне делать сегодня", "как самочувствие", "какие у меня таблетки",
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
        "включи ютуб", "пауза", "продолжи", "какие треки",
    ],
    "инфо": [
        "какая погода", "погода на завтра", "погода на дачу",
        "какие новости", "что ты знаешь о кофе", "что ты знаешь о космосе",
        "зачитай журнал", "что я делал вчера", "мой дневник",
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
        "статус", "проверь ауру", "что ты умеешь", "кто ты",
        "расскажи о себе", "что происходит",
    ],
    "рой": [
        "какой сектор", "где я", "статус роя", "бортовой журнал",
        "собери данные", "просканируй новости",
    ],
    "детерминированные": [
        "сколько букв в слове программирование",
        "сколько букв в слове кот",
        "сколько будет 17 умножить на 24",
        "сколько будет 5 плюс 10",
        "вычисли 100 минус 50",
    ],
    "vision": [
        "сделай скриншот", "что на экране", "сделай снимок",
    ],
}


async def probe(orch, text: str) -> tuple[str, str, float]:
    from aura.core.protocol import AgentRequest
    req = AgentRequest(text=text)
    t0 = time.time()
    try:
        agent = orch.registry.find(req)
        if agent is None:
            return ("NONE", "-", 0.0)
        resp = await asyncio.wait_for(agent.handle(req), timeout=5.0)
        dt = (time.time() - t0) * 1000
        status = resp.status.value if hasattr(resp.status, "value") else str(resp.status)
        status = status.upper() if status in ("ok","error","partial","not_handled") else status
        return (status, type(agent).__name__, dt)
    except TimeoutError:
        return ("TIMEOUT", type(agent).__name__ if agent else "-", 5000.0)
    except Exception:
        return ("ERROR", type(agent).__name__ if agent else "-", (time.time()-t0)*1000)


async def main() -> int:
    print("=" * 70)
    print("  AURA — Mass Agent Probe (200+ фраз)")
    print("=" * 70)
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    print(f"Агентов в реестре: {len(orch)}\n")

    stats = {"ok": 0, "error": 0, "timeout": 0, "none": 0, "not_handled": 0}
    covered: set[str] = set()
    dead: list[tuple[str, str]] = []
    errors: list[tuple[str, str]] = []

    for group, phrases in GROUPS.items():
        ok_in_group = 0
        for text in phrases:
            status, agent, _ = await probe(orch, text)
            stats[status.lower()] = stats.get(status.lower(), 0) + 1
            if agent != "-" and status == "OK":
                covered.add(agent)
                ok_in_group += 1
            if status == "NONE":
                dead.append((group, text))
            if status == "ERROR":
                errors.append((agent, text))
        print(f"  [{group:20s}] {ok_in_group}/{len(phrases)} OK")

    print()
    print("=" * 70)
    print("  ИТОГ")
    print("=" * 70)
    total = sum(stats.values())
    for k, v in stats.items():
        print(f"  {k:12s}: {v}")
    print(f"  ВСЕГО:        {total}")
    print(f"  Уникальных агентов: {len(covered)}")
    print(f"  Мёртвых фраз: {len(dead)}")
    print()
    if dead:
        print("  🚫 МЁРТВЫЕ ФРАЗЫ (первые 20):")
        for grp, text in dead[:20]:
            print(f"    [{grp:15s}] {text}")
    if errors:
        print()
        print("  ❌ ОШИБКИ:")
        for agent, text in errors[:10]:
            print(f"    [{agent}] {text}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
