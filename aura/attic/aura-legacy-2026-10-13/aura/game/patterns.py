"""Patterns — база знаний о фиксах.

Strategy = ключ оружия из ask_strategy():
  recon | patch | rewrite | autofix | reset | defer

Наука: Alexander 1977 (Pattern Language).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Pattern:
    code: str
    title: str
    why: str
    science: str
    code_before: str
    code_after: str
    strategy: str          # recon | patch | rewrite | autofix | reset | defer
    difficulty: int


PATTERNS: dict[str, Pattern] = {
    "F541": Pattern(
        "F541", "f-string без placeholder",
        "Строка помечена f'', но без {переменных}. Префикс лишний.",
        "pyflakes F541 — статический анализ строк.",
        'raise ValueError(f"some error")',
        'raise ValueError("some error")',
        "patch", 1,
    ),
    "F401": Pattern(
        "F401", "Unused import",
        "Модуль импортирован, но не используется.",
        "Saltzer & Schroeder 1975 — least privilege.",
        "import os\nimport sys  # не используется",
        "import os",
        "autofix", 1,
    ),
    "E501": Pattern(
        "E501", "Строка слишком длинная",
        "Строка >88 символов. Читать неудобно.",
        "PEP 8 — 79/88 символов обоснованы терминалом.",
        "result = some_function(a, b, c, d, e, f)",
        "result = some_function(\n    a, b, c, d, e, f,\n)",
        "patch", 2,
    ),
    "SIM105": Pattern(
        "SIM105", "try/except/pass → contextlib.suppress",
        "Если try нужен только проглотить — suppress чище.",
        "Ruff SIM105 — explicit лучше implicit (PEP 20).",
        "try:\n    conn.close()\nexcept Exception:\n    pass",
        "with contextlib.suppress(Exception):\n    conn.close()",
        "patch", 2,
    ),
    "UP017": Pattern(
        "UP017", "timezone.utc → UTC",
        "Python 3.11 добавил datetime.UTC.",
        "PEP 615 — UTC alias как стандарт.",
        "now = datetime.now(timezone.utc)",
        "now = datetime.now(UTC)",
        "autofix", 1,
    ),
    "B023": Pattern(
        "B023", "Loop variable в замыкании",
        "Замыкание захватывает переменную по ссылке.",
        "Bug 74 в CPython — классика функций в цикле.",
        "for tpl in templates:\n    def repl(m):\n        return tpl.format(m)",
        "for tpl in templates:\n    def repl(m, tpl=tpl):\n        return tpl.format(m)",
        "rewrite", 3,
    ),
    "RUF022": Pattern(
        "RUF022", "__all__ не отсортирован",
        "Ruff хочет isort-style сортировку.",
        "Ruff RUF022 — стиль из isort.",
        '__all__ = ["B", "A", "C"]',
        '__all__ = ["A", "B", "C"]',
        "autofix", 1,
    ),
}

DEFAULT_PATTERN = Pattern(
    "?", "Неизвестный баг",
    "Паттерн не описан. Сначала разведка.",
    "Д9: не гадать — сначала диагностика.",
    "(неизвестно)", "(после разведки)",
    "recon", 3,
)


def pattern_for(code: str) -> Pattern:
    return PATTERNS.get(code, DEFAULT_PATTERN)


def has_pattern(code: str) -> bool:
    return code in PATTERNS


__all__ = [
    "DEFAULT_PATTERN", "PATTERNS", "Pattern",
    "has_pattern", "pattern_for",
]
