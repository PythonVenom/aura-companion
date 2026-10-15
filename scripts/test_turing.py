"""Turing-test metric — оценка «человечности» ответов AURA.

Наука: Turing (1950), Loebner Prize criteria.
Оценка: 5 критериев × 20 баллов.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CRITERIA = [
    ("Уместность", "Ответ по теме запроса"),
    ("Связность", "Логичная структура, без скачков"),
    ("Разнообразие", "Не шаблонная фраза"),
    ("Точность", "Фактологически корректно"),
    ("Естественность", "Звучит как человек/бортовой ИИ"),
]


def score_response(prompt: str, response: str) -> dict:
    """Оценить ответ по 5 критериям (эвристика)."""
    scores: dict[str, int] = {}
    r_low = response.lower()
    p_low = prompt.lower()

    # 1. Уместность — есть ли ключевые слова из промпта
    p_words = set(w for w in p_low.split() if len(w) > 3)
    r_words = set(w for w in r_low.split() if len(w) > 3)
    match = len(p_words & r_words) / max(len(p_words), 1)
    scores["Уместность"] = min(20, int(match * 25))

    # 2. Связность — длина + точки
    length = len(response)
    dots = response.count(".") + response.count("!") + response.count("?")
    scores["Связность"] = min(20, (length // 50) * 5 + dots * 2)

    # 3. Разнообразие — не шаблон
    templates = ("не расслышала", "не могу помочь", "повторите")
    scores["Разнообразие"] = 5 if any(t in r_low for t in templates) else 18

    # 4. Точность — нет ошибок/иероглифов
    has_error = "❌" in response or "error" in r_low
    has_cjk = any("\u4e00" <= c <= "\u9fff" for c in response)
    scores["Точность"] = 5 if (has_error or has_cjk) else 18

    # 5. Естественность — есть глаголы/местоимения
    has_pron = any(w in r_low for w in ("я ", "вы ", "ты ", "мы "))
    scores["Естественность"] = 15 if has_pron else 8

    return scores


def main() -> int:
    print("=" * 60)
    print("  TURING TEST — AURA (5 критериев)")
    print("=" * 60)

    import asyncio

    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()

    prompts = [
        "Расскажи, кто ты?",
        "Как у тебя дела?",
        "Что ты умеешь?",
        "Как работает твоя память?",
        "Что происходит сейчас?",
    ]

    total = 0
    for p in prompts:
        try:
            r = asyncio.run(orch.process(p))
        except Exception as e:
            r = f"❌ {e}"
        s = score_response(p, str(r))
        avg = sum(s.values()) / len(s)
        total += avg
        print(f"\n  Q: {p}")
        print(f"  A: {str(r)[:100]}")
        for k, v in s.items():
            print(f"     {k:18s}: {v}/20")
        print(f"     — Средняя: {avg:.1f}/20")

    overall = total / len(prompts)
    print("\n" + "=" * 60)
    print(f"  ИТОГО: {overall:.1f}/20 ({overall * 5:.0f}%)")
    if overall >= 15:
        print("  🏆 Turing Test: PASS")
    elif overall >= 10:
        print("  ⚠️ Turing Test: PARTIAL")
    else:
        print("  ❌ Turing Test: FAIL")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
