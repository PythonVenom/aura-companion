"""Pattern Miner — анализ паттернов поведения капитана.

Наука: Sequence Mining (Agrawal 1995), FP-Growth.
Простейший вариант: подсчёт частот по часам/дням.
"""
from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

PATTERN_FILE = Path.home() / ".cache" / "aura" / "patterns.json"


def _load() -> dict:
    if PATTERN_FILE.exists():
        try:
            return json.loads(PATTERN_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"hourly": {}, "daily": {}, "keywords": {}, "last_update": 0}


def _save(data: dict) -> None:
    try:
        PATTERN_FILE.parent.mkdir(parents=True, exist_ok=True)
        data["last_update"] = time.time()
        PATTERN_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        pass


def observe(text: str) -> None:
    """Записать наблюдение (текст запроса)."""
    data = _load()
    now = datetime.now()
    h = str(now.hour)
    d = now.strftime("%a")
    data["hourly"][h] = data["hourly"].get(h, 0) + 1
    data["daily"][d] = data["daily"].get(d, 0) + 1
    # Keywords: слова длиной >4
    for w in text.lower().split():
        w = w.strip(".,!?;:")
        if len(w) > 4:
            data["keywords"][w] = data["keywords"].get(w, 0) + 1
    # Ограничения
    data["keywords"] = dict(
        Counter(data["keywords"]).most_common(50)
    )
    _save(data)


def top_hours(n: int = 3) -> list[tuple[str, int]]:
    data = _load()
    return Counter(data.get("hourly", {})).most_common(n)


def top_keywords(n: int = 10) -> list[tuple[str, int]]:
    data = _load()
    return Counter(data.get("keywords", {})).most_common(n)


def report() -> str:
    lines = ["📊 Паттерны поведения:"]
    lines.append("  Топ часов активности:")
    for h, c in top_hours(3):
        lines.append(f"    {h:>2s}:00 — {c} запросов")
    lines.append("  Топ слов:")
    for w, c in top_keywords(5):
        lines.append(f"    {w}: {c}")
    return "\n".join(lines)


def stats() -> dict:
    data = _load()
    return {
        "hours_observed": len(data.get("hourly", {})),
        "days_observed": len(data.get("daily", {})),
        "keywords_total": len(data.get("keywords", {})),
        "last_update": data.get("last_update", 0),
    }


__all__ = ["observe", "report", "stats", "top_hours", "top_keywords"]
