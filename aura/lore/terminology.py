"""Словарь замен: техническое → игровое (Mass Effect).

Правило: ни одно техническое слово не должно звучать вслух.
ruff → энергоблок, pytest → узлы, branch → сектор.
"""

from __future__ import annotations

import re

# Порядок важен: длинные паттерны первыми
TERMS: dict[str, str] = {
    r"\bruff\b": "энергоблок",
    r"\bpytest\b": "диагностика корпуса",
    r"\btests?\b": "узлы",
    r"\bbranch\b": "сектор",
    r"\bcommit(s|ted)?\b": "координаты",
    r"\bbug(s)?\b": "пробоина",
    r"\bfix(es|ed)?\b": "залп",
    r"\bagent(s)?\b": "модуль",
    r"\bmodule(s)?\b": "модуль",
    r"\bcheck(s|ed)?\b": "сканирование",
    r"\bpassed\b": "в норме",
    r"\bfailed\b": "повреждено",
}


def translate(text: str) -> str:
    """Заменяет технические термины на игровые (регистронезависимо)."""
    if not text:
        return text
    out = text
    for pattern, replacement in TERMS.items():
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    return out
