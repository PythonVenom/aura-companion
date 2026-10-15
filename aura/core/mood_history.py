"""Mood History — история настроений AURA по дням.

Наука: Mood Tracking (Bolger 2003), Time Series.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MOOD_FILE = Path.home() / ".cache" / "aura" / "mood_history.json"


@dataclass
class MoodPoint:
    date: str
    emotion: str
    calm: float
    alert: float
    warm: float
    curious: float
    focused: float


def _load() -> list[dict]:
    if MOOD_FILE.exists():
        try:
            return json.loads(MOOD_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save(data: list[dict]) -> None:
    try:
        MOOD_FILE.parent.mkdir(parents=True, exist_ok=True)
        MOOD_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        pass


def snapshot() -> MoodPoint | None:
    """Записать снимок настроения."""
    try:
        from aura.core.emotion_evolution import get_state
        s = get_state()
    except Exception:
        return None
    point = MoodPoint(
        date=datetime.now().strftime("%Y-%m-%d"),
        emotion=s.dominant(),
        calm=round(s.calm, 3),
        alert=round(s.alert, 3),
        warm=round(s.warm, 3),
        curious=round(s.curious, 3),
        focused=round(s.focused, 3),
    )
    data = _load()
    # Заменить сегодняшний, если есть
    data = [d for d in data if d.get("date") != point.date]
    data.append(point.__dict__)
    data = data[-30:]
    _save(data)
    return point


def sparkline(values: list[float], width: int = 20) -> str:
    """Простой sparkline в ASCII."""
    if not values:
        return "─" * width
    chars = "▁▂▃▄▅▆▇█"
    mn, mx = min(values), max(values)
    if mx == mn:
        return chars[4] * width
    out = []
    for v in values[-width:]:
        idx = int((v - mn) / (mx - mn) * (len(chars) - 1))
        out.append(chars[idx])
    return "".join(out)


def report(days: int = 7) -> str:
    data = _load()[-days:]
    if not data:
        return "📊 Нет данных о настроении"
    lines = [f"📊 Настроение за {len(data)} дн.:"]
    for key in ("calm", "alert", "warm", "curious", "focused"):
        vals = [d.get(key, 0.5) for d in data]
        lines.append(f"  {key:8s} {sparkline(vals)}  avg={sum(vals)/len(vals):.2f}")
    latest = data[-1]
    lines.append(f"  Эмоция: {latest.get('emotion')} ({latest.get('date')})")
    return "\n".join(lines)


def stats() -> dict:
    data = _load()
    return {"days": len(data), "last": data[-1]["date"] if data else None}


__all__ = ["MoodPoint", "report", "snapshot", "sparkline", "stats"]
