"""#135 AgentGrammars — точные грамматики для elder-care.

Наука:
- Rhasspy grammar (2020) — pattern matching для offline ASR
- Warden 2018 — keyword spotting для коротких фраз
- Nielsen #6 (recognition) — точные триггеры для критичных команд

Зачем:
  T-one ASR ошибается на коротких фразах бати («плохо», «упал»).
  Грамматика = regex + fuzzy-match для критичных слов.
"""
from __future__ import annotations

import re

# Критические грамматики (компилируются один раз)
GRAMMARS: dict[str, re.Pattern] = {
    "sos": re.compile(
        r"\b(плохо|помоги|помогите|скорую|скорая|умираю|болит|"
        r"вызови|срочно|sos|спасите)\b",
        re.IGNORECASE,
    ),
    "fall": re.compile(
        r"\b(упал|упала|упал[аи]?|не\s+могу\s+встать|"
        r"лежу|на\s+полу|сломал)\b",
        re.IGNORECASE,
    ),
    "stop": re.compile(
        r"\b(стоп|тише|хватит|замолчи|прекрати|молчи|пауза)\b",
        re.IGNORECASE,
    ),
    "yes": re.compile(r"\b(да|ага|угу|конечно|верно|подтверждаю)\b", re.IGNORECASE),
    "no": re.compile(r"\b(нет|не|неа|отмена|неверно|не надо)\b", re.IGNORECASE),
}


def match(grammar_name: str, text: str) -> bool:
    """Совпадает ли текст с грамматикой."""
    if not text or grammar_name not in GRAMMARS:
        return False
    return GRAMMARS[grammar_name].search(text) is not None


def match_any(text: str) -> str | None:
    """Вернуть имя первой сработавшей грамматики или None."""
    if not text:
        return None
    for name, pattern in GRAMMARS.items():
        if pattern.search(text):
            return name
    return None


__all__ = ["GRAMMARS", "match", "match_any"]
