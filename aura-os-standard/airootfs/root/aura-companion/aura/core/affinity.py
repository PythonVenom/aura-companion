"""Affinity — уровень отношений AURA с капитаном (Cortana-style).

Наука: Social Penetration Theory (Altman 1973), AIsis affinity.
Растёт от общения, НЕ влияет на субординацию (бортовой компьютер).
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

AFFINITY_FILE = Path.home() / ".cache" / "aura" / "affinity.json"


@dataclass
class Affinity:
    """Уровень отношений."""
    level: int = 0
    xp: int = 0
    last_interaction: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def rank(self) -> str:
        return {
            0: "Знакомство",
            1: "Сотрудничество",
            2: "Доверие",
            3: "Опора",
            4: "Легенда",
        }.get(min(self.level, 4), "Легенда")

    @property
    def next_xp(self) -> int:
        return (self.level + 1) * 100


_AFFINITY: Affinity | None = None


def _load() -> Affinity:
    if AFFINITY_FILE.exists():
        try:
            data = json.loads(AFFINITY_FILE.read_text(encoding="utf-8"))
            return Affinity(**{k: v for k, v in data.items() if k in Affinity.__dataclass_fields__})
        except Exception:
            pass
    return Affinity()


def _save(a: Affinity) -> None:
    try:
        AFFINITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        AFFINITY_FILE.write_text(json.dumps(asdict(a), ensure_ascii=False, indent=2))
    except Exception:
        pass


def get_affinity() -> Affinity:
    global _AFFINITY
    if _AFFINITY is None:
        _AFFINITY = _load()
    return _AFFINITY


def add_xp(amount: int = 1, note: str = "") -> Affinity:
    """Добавить опыт. Level растёт каждые 100 XP."""
    a = get_affinity()
    a.xp += amount
    a.last_interaction = time.time()
    if note:
        a.notes.append(note)
        a.notes = a.notes[-20:]
    while a.xp >= a.next_xp and a.level < 4:
        a.level += 1
    _save(a)
    return a


def status() -> str:
    a = get_affinity()
    return (
        f"🤝 {a.rank} (уровень {a.level})\n"
        f"   XP: {a.xp}/{a.next_xp}\n"
        f"   Взаимодействий: {len(a.notes)}"
    )


__all__ = ["Affinity", "add_xp", "get_affinity", "status"]
