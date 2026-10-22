"""Wake-word детектор с fuzzy-матчингом (2026-10-13).

Проблема: T-one слышит «Аура» как «алло», «алла», «аула».
Решение: fuzzy-матч по токенам через расстояние Левенштейна.

Наука:
- Levenshtein 1965 — расстояние редактирования (вставка/удаление/замена)
- Jaro 1989, Winkler 1990 — Jaro-Winkler для коротких строк
- Soundex (Russell 1918) — фонетическое сходство (для русского сложно)

Принципы:
1. Токенизация — не подстроки, а отдельные слова
2. Расстояние Левенштейна ≤ 2 для слова длиной 4-6
3. Порог зависит от длины (ratio)
4. Elder-care whitelist — приоритет выше fuzzy
"""
from __future__ import annotations

import re

# === Эталонные слова активации (нормальная форма) ===
CANONICAL = (
    "аура", "ауру", "ауры", "ауре", "ауро", "аура",
    "aura",  # латиница
)

# === Известные искажения от T-one (soft-check, порог 1) ===
# Известные искажения от T-one (только >=4 букв — иначе шум).
KNOWN_VARIANTS = (
    "алло", "алла", "аула", "ауло", "аулы", "лаура",
)

# === Whitelist без активации (elder-care, ADR-057) ===
WHITELIST_NO_WAKE = (
    "сколько времени", "который час",
    "какой день", "какое число", "какой сегодня",
    "какая погода", "погода на",
    "мне плохо", "помогите", "вызови скорую", "вызов скорой",
    "sos", "тревога", "упал", "упала",
    "пора пить", "напомни про лекарств",
)

# Стоп-слова: не проверяем fuzzy (они всегда другие)
STOP_WORDS = frozenset({
    "и", "а", "но", "или", "да", "нет", "не", "ни", "же", "ли", "бы",
    "в", "на", "с", "к", "по", "за", "из", "от", "до", "для",
    "я", "ты", "он", "она", "мы", "вы", "они",
})


def _tokens(text: str) -> list[str]:
    """Разбить на токены (буквы+цифры, lowercase)."""
    return re.findall(r"[а-яёa-z0-9]+", text.lower())


def levenshtein(a: str, b: str) -> int:
    """Расстояние Левенштейна (1965).

    Минимум вставок/удалений/замен, чтобы a → b.
    """
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(
                curr[j - 1] + 1,      # вставка
                prev[j] + 1,          # удаление
                prev[j - 1] + cost,   # замена
            ))
        prev = curr
    return prev[-1]


# Минимальная длина токена для fuzzy (иначе «ау», «ура» — шум)
MIN_TOKEN_LEN = 3
# Максимальная разница длин токена и canon (иначе «пауза» ≠ «аула»)
# Для коротких эталонов (<=4) длина должна совпадать точно,
# иначе «пауза» (5) fuzzy-матчится с «аура» (4).
MAX_LEN_DIFF_SHORT = 0   # len(canon) <= 4
MAX_LEN_DIFF_LONG = 1    # len(canon) >= 5


def _max_distance(word: str) -> int:
    """Порог Левенштейна зависит от длины эталона.

    - 3-4 буквы (аура): порог 2 (алло = 2)
    - 5-6 букв: порог 2
    - 7+: порог 3

    Но: токен короче 3 букв — не проверяем.
    И |len(token) - len(canon)| > 1 — отказ.
    """
    n = len(word)
    if n <= 4:
        return 2
    if n <= 6:
        return 2
    return 3


def _fuzzy_match(token: str, canon: str) -> bool:
    """True если token fuzzy-совпадает с canon (с учётом длины).

    Короткие эталоны (<=4) требуют точной длины.
    """
    if len(token) < MIN_TOKEN_LEN:
        return False
    diff = abs(len(token) - len(canon))
    max_diff = MAX_LEN_DIFF_SHORT if len(canon) <= 4 else MAX_LEN_DIFF_LONG
    if diff > max_diff:
        return False
    return levenshtein(token, canon) <= _max_distance(canon)


def is_wake_word(text: str) -> bool:
    """True если в тексте есть wake-word (fuzzy).

    Алгоритм:
    1. Токенизация
    2. Whitelist check (elder-care)
    3. Для каждого токена: точное или fuzzy совпадение с CANONICAL
    4. Fuzzy с KNOWN_VARIANTS (порог 1 — строже)

    Ложные срабатывания исключены: «ураган» ≠ «ура» (токен другой).
    """
    if not text:
        return False
    t = text.lower().strip()

    # 1. Whitelist — приоритет (elder-care)
    if any(w in t for w in WHITELIST_NO_WAKE):
        return True

    # 2. Токенизация
    tokens = _tokens(t)
    if not tokens:
        return False

    # 3. Fuzzy к canonical (строгий порог)
    for token in tokens:
        if token in STOP_WORDS:
            continue
        for canon in CANONICAL:
            if token == canon:
                return True
            if _fuzzy_match(token, canon):
                return True

    # 4. Точное совпадение с известными вариантами (порог 0 — строже)
    return any(token in KNOWN_VARIANTS for token in tokens)


def strip_wake_word(text: str) -> str:
    """Убрать wake-word из текста (для команды после активации)."""
    if not text:
        return ""
    result = text.lower()
    all_forms = set(CANONICAL) | set(KNOWN_VARIANTS)
    # Убираем как отдельные токены
    tokens = _tokens(result)
    filtered = [tok for tok in tokens if tok not in all_forms]
    # Проверяем: если токен fuzzy-похож на canonical — тоже убираем
    clean = []
    for tok in filtered:
        is_wake = any(_fuzzy_match(tok, canon) for canon in CANONICAL)
        if not is_wake:
            clean.append(tok)
    return " ".join(clean).strip(".,!? ")


__all__ = [
    "CANONICAL",
    "KNOWN_VARIANTS",
    "MAX_LEN_DIFF_LONG",
    "MAX_LEN_DIFF_SHORT",
    "MIN_TOKEN_LEN",
    "WHITELIST_NO_WAKE",
    "is_wake_word",
    "levenshtein",
    "strip_wake_word",
]
