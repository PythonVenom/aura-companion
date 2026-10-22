#!/usr/bin/env python3
"""Capability Matrix — аудит покрытия агентов Aura."""
import sys
import asyncio
import importlib
import pkgutil
from pathlib import Path

sys.path.insert(0, str(Path.home() / "aura_project"))

# Тестовые фразы по категориям
PHRASES = {
    "info.time":        ["который час", "сколько времени"],
    "info.date":        ["какой сегодня день", "какое число"],
    "info.weather":     ["какая погода", "чё на улице", "дождь будет"],
    "info.currency":    ["курс доллара", "сколько стоит евро"],
    "info.news":        ["новости", "что нового"],
    "comm.telegram":    ["позвони сыну", "напиши в телеграм"],
    "comm.vk":          ["открой вк", "что нового в вк"],
    "comm.ok":          ["одноклассники"],
    "comm.rutube":      ["рутуб", "открой рутуб"],
    "fun.music":        ["включи музыку", "поставь песню"],
    "fun.radio":        ["включи радио", "радио маяк"],
    "fun.movie":        ["включи фильм", "найди фильм"],
    "fun.prev_track":   ["предыдущий трек", "верни песню"],
    "rem.pill":         ["напомни таблетку", "пора пить"],
    "rem.timer":        ["напомни через час", "таймер 10 минут"],
    "sos":              ["мне плохо", "помогите", "вызови скорую"],
    "ctrl.stop":        ["аура стоп", "тихо"],
    "ctrl.repeat":      ["аура повтори"],
    "ctrl.present":     ["аура ты тут", "ты здесь"],
}


async def probe(intent: str, phrase: str) -> dict:
    result = {"intent": intent, "phrase": phrase, "status": "?", "answer": ""}
    try:
        from aura.core.orchestrator import Orchestrator
        # Создаём orch минимально
        orch_mod = importlib.import_module("aura.core.orchestrator")
        # Ищем класс с process
        cls = None
        for name in dir(orch_mod):
            obj = getattr(orch_mod, name)
            if isinstance(obj, type) and hasattr(obj, "process"):
                cls = obj
                break
        if cls is None:
            result["status"] = "NO_ORCHESTRATOR"
            return result
        # Пытаемся создать и вызвать
        try:
            orch = cls()
        except Exception as e:
            result["status"] = f"INIT_FAIL: {e}"
            return result
        try:
            ans = orch.process(phrase)
            if asyncio.iscoroutine(ans):
                ans = await ans
            result["answer"] = str(ans)[:80]
            result["status"] = "OK"
        except Exception as e:
            result["status"] = f"PROCESS_FAIL: {e}"
    except Exception as e:
        result["status"] = f"IMPORT_FAIL: {e}"
    return result


async def main():
    print("=" * 80)
    print("CAPABILITY MATRIX — Aura Coverage Audit")
    print("=" * 80)
    print(f"{'INTENT':<20} {'STATUS':<15} {'ANSWER':<45}")
    print("-" * 80)
    for intent, phrases in PHRASES.items():
        r = await probe(intent, phrases[0])
        ans = r["answer"].replace("\n", " ")[:43]
        print(f"{intent:<20} {r['status']:<15} {ans:<45}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
