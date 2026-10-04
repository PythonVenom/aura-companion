"""NLP: fuzzy matching для ASR."""
from __future__ import annotations


def _levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[j-1] + 1, prev[j] + 1,
                           prev[j-1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _adaptive_dist(keyword: str) -> int:
    """Адаптивный max_dist по длине keyword.

    Короткие (<=4) — строго, иначе ложные срабатывания.
    Средние (5-7) — 1 правка.
    Длинные (8+) — 2 правки (ASR чаще ошибается в длинных словах).
    """
    n = len(keyword)
    if n <= 4:
        return 0
    if n <= 7:
        return 1
    return 2


def fuzzy_match(text, keywords, max_dist=None):
    """True если любое keyword похоже на слово в text.

    max_dist=None → адаптивно по длине keyword.
    """
    if isinstance(keywords, str):
        keywords = (keywords,)
    words = text.lower().split()
    text_low = text.lower()
    for kw in keywords:
        kw_low = kw.lower()
        if kw_low in text_low:
            return True
        md = max_dist if max_dist is not None else _adaptive_dist(kw_low)
        if md == 0:
            continue  # только substring выше
        for w in words:
            if abs(len(w) - len(kw_low)) > md:
                continue
            if _levenshtein(w, kw_low) <= md:
                return True
    return False
