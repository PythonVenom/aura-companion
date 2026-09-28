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


def fuzzy_match(text, keywords, max_dist=2):
    if isinstance(keywords, str):
        keywords = (keywords,)
    words = text.lower().split()
    text_low = text.lower()
    for kw in keywords:
        kw_low = kw.lower()
        if kw_low in text_low:
            return True
        for w in words:
            if abs(len(w) - len(kw_low)) > max_dist:
                continue
            if _levenshtein(w, kw_low) <= max_dist:
                return True
    return False
