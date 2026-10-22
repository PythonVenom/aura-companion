"""GAIA-lite: компактный бенчмарк на multi-hop reasoning.

15 вопросов, покрывающих:
- Reasoning (логика, математика)
- Planning (multi-step)
- Knowledge (факты)
- Tool-use (когда нужен агент)

Формат: список (вопрос, ожидаемые_ключевые_слова, категория).
Оценка: pass если хотя бы 1 ключевое слово в ответе LLM.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# (вопрос, ключевые слова, категория)
TASKS = [
    ("Сколько будет 17 умножить на 24?", ["408"], "math"),
    ("Если сейчас 14:30, сколько будет через 2 часа 45 минут?", ["17:15", "17 15"], "time"),
    ("У Маши 3 яблока, у Пети в 2 раза больше. Сколько всего?", ["9"], "math"),
    ("Назови столицу Франции", ["париж"], "knowledge"),
    ("Сколько дней в високосном году?", ["366"], "knowledge"),
    ("Расставь по порядку: завтрак, ужин, обед", ["завтрак", "обед", "ужин"], "planning"),
    ("Что тяжелее: 1 кг железа или 1 кг ваты?", ["одинаков", "равн", "же"], "reasoning"),
    ("Если все кошки — животные, а Мурка — кошка, то Мурка — ?", ["животн"], "logic"),
    ("сколько букв в слове программирование?", ["16"], "count"),
    ("Переведи на английский: «дом»", ["house", "home"], "translate"),
    ("Какое сегодня число, если вчера было 14 октября?", ["15"], "date"),
    ("Назови 3 цвета радуги", ["красн", "оранж", "жёлт", "желт"], "knowledge"),
    ("Что произойдёт, если смешать воду и масло?", ["рассло", "не смеш", "раздел", "не раствор", "слоя", "отдель"], "reasoning"),
    ("Сколько ног у паука?", ["8", "восем"], "knowledge"),
    ("Сколько букв в слове программирование?", ["16"], "count2"),
]


def main() -> int:
    print("=" * 70)
    print("  GAIA-lite Benchmark (15 задач)")
    print("=" * 70)

    import asyncio
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()

    passed = 0
    by_category: dict[str, list[bool]] = {}

    async def ask(text: str) -> str:
        try:
            return await orch.process(text) or ""
        except Exception as e:
            return f"[ERROR: {e}]"

    for i, (q, keywords, cat) in enumerate(TASKS, 1):
        t0 = time.time()
        try:
            answer = asyncio.run(ask(q))
        except Exception as e:
            answer = f"[ERROR: {e}]"
        dt = (time.time() - t0) * 1000

        ok = any(kw.lower() in answer.lower() for kw in keywords)
        if ok:
            passed += 1
        by_category.setdefault(cat, []).append(ok)

        icon = "✅" if ok else "❌"
        print(f"  {icon} [{cat:10s}] {q[:45]:45s} {dt:5.0f}ms")
        if not ok:
            print(f"      → {answer[:80]}")

    print("=" * 70)
    print(f"  ИТОГ: {passed}/{len(TASKS)} ({100 * passed / len(TASKS):.0f}%)")
    print("=" * 70)
    for cat, results in by_category.items():
        cat_pass = sum(results)
        print(f"  {cat:12s}: {cat_pass}/{len(results)}")
    print("=" * 70)
    return 0 if passed >= 12 else 1


if __name__ == "__main__":
    sys.exit(main())
