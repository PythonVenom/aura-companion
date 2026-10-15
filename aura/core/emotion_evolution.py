"""Emotion Evolution — эмоции AURA растут через опыт (NieR-style).

Наука: Affective Computing (Picard 1997), Emotion ML (Poria 2017).
Каждое событие → сдвиг эмоционального состояния.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

EMO_FILE = Path.home() / ".cache" / "aura" / "emotions.json"


@dataclass
class EmotionState:
    # 5 базовых измерений (0.0 .. 1.0)
    calm: float = 0.5
    alert: float = 0.3
    warm: float = 0.5
    curious: float = 0.5
    focused: float = 0.5
    history: list[dict] = field(default_factory=list)

    def dominant(self) -> str:
        dims = {
            "calm": self.calm,
            "alert": self.alert,
            "warm": self.warm,
            "curious": self.curious,
            "focused": self.focused,
        }
        return max(dims, key=dims.get)  # type: ignore[arg-type]


_STATE: EmotionState | None = None


def _load() -> EmotionState:
    if EMO_FILE.exists():
        try:
            data = json.loads(EMO_FILE.read_text(encoding="utf-8"))
            return EmotionState(**{k: v for k, v in data.items()
                                   if k in EmotionState.__dataclass_fields__})
        except Exception:
            pass
    return EmotionState()


def _save(s: EmotionState) -> None:
    try:
        EMO_FILE.parent.mkdir(parents=True, exist_ok=True)
        EMO_FILE.write_text(json.dumps(asdict(s), ensure_ascii=False, indent=2))
    except Exception:
        pass


def get_state() -> EmotionState:
    global _STATE
    if _STATE is None:
        _STATE = _load()
    return _STATE


EVENT_DELTAS: dict[str, dict[str, float]] = {
    "sos":      {"alert": +0.3, "calm": -0.2},
    "fall":     {"alert": +0.4, "calm": -0.3},
    "greeting": {"warm": +0.1, "calm": +0.05},
    "thanks":   {"warm": +0.15},
    "question": {"curious": +0.1},
    "task":     {"focused": +0.15},
    "idle":     {"calm": +0.1, "alert": -0.05},
    "error":    {"alert": +0.2, "focused": +0.1},
    "success":  {"calm": +0.1, "focused": +0.1},
}


def evolve(event: str) -> EmotionState:
    """Сдвинуть эмоции по событию."""
    s = get_state()
    delta = EVENT_DELTAS.get(event, {})
    for dim, dv in delta.items():
        cur = getattr(s, dim, 0.5)
        new = max(0.0, min(1.0, cur + dv))
        setattr(s, dim, new)
    s.history.append({"event": event, "ts": time.time()})
    s.history = s.history[-50:]
    _save(s)
    return s


def decay(rate: float = 0.02) -> EmotionState:
    """Медленное возвращение к нейтрали (homeostasis)."""
    s = get_state()
    for dim in ("calm", "alert", "warm", "curious", "focused"):
        cur = getattr(s, dim, 0.5)
        new = cur + (0.5 - cur) * rate
        setattr(s, dim, round(new, 4))
    _save(s)
    return s


def status() -> str:
    s = get_state()
    return (
        f"😌 Доминирует: {s.dominant()}\n"
        f"   calm={s.calm:.2f} alert={s.alert:.2f} warm={s.warm:.2f}\n"
        f"   curious={s.curious:.2f} focused={s.focused:.2f}\n"
        f"   Событий: {len(s.history)}"
    )


__all__ = ["EVENT_DELTAS", "EmotionState", "decay", "evolve", "get_state", "status"]
