"""Живое тестирование elder-care агентов AURA.

Сценарии: SOS, Fall, Meds, Call, FinElder.
Запуск:
    export PYTHONPATH=$PWD
    ./venv/bin/python scripts/test_elder.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


SCENARIOS = [
    ("SOS", "аура помоги мне срочно", "Вызываю помощь"),
    ("Fall", "я упал не могу встать", "SOS"),
    ("Meds", "напомни выпить таблетки в 20:00", "Запомнила"),
    ("Call", "позвони сыну", "Telegram"),
    ("FinElder", "проверь мои финансы", "FinElder"),
]


async def run_scenario(orch, name: str, text: str, expected: str) -> bool:
    print(f"\n[{name}] Запрос: {text!r}")
    try:
        response = await orch.process(text)
        print(f"  Ответ: {response!r}")
        matched = expected in str(response)
        print(f"  {'✅' if matched else '❌'} ожидался {expected}")
        return matched
    except Exception as e:
        print(f"  ❌ Ошибка: {type(e).__name__}: {e}")
        return False


async def main() -> int:
    print("=" * 60)
    print("  AURA Elder-care Live Test")
    print("=" * 60)

    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    print(f"Агентов: {len(orch)}")

    ok = 0
    for name, text, expected in SCENARIOS:
        if await run_scenario(orch, name, text, expected):
            ok += 1

    print("\n" + "=" * 60)
    print(f"  Итого: {ok}/{len(SCENARIOS)}")
    print("=" * 60)
    return 0 if ok == len(SCENARIOS) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
