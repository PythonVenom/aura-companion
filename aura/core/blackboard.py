"""Blackboard — общая рабочая память 107 агентов (стигмергия).

Наука:
- Stigmergy (Grasse 1959) — координация через следы в среде
- Blackboard Architecture (Erman 1980, Hayes-Roth 1985)
- Emergent Communication (MARL, Foerster 2016)

Идея: агенты не общаются напрямую. Они пишут «следы» на доску
и читают чужие. Рой сам собирается вокруг задачи.

Структура (JSON):
{
  "sector": "health",           # текущий сектор
  "alerts": [{agent, level, ts, text}],
  "tasks":  [{agent, status, eta, text}],
  "facts":  {key: value},       # общие факты (настроение, контекст)
  "trail":  [{from, to, ts, action}],  # кто кого вызывал (граф)
  "ts": 1729...                 # последнее обновление
}
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

BOARD_PATH = Path.home() / ".cache" / "aura" / "blackboard.json"
_LOCK = threading.Lock()


def _empty() -> dict[str, Any]:
    return {
        "sector": "unknown",
        "alerts": [],
        "tasks": [],
        "facts": {},
        "trail": [],
        "ts": time.time(),
    }


def _read() -> dict[str, Any]:
    try:
        if BOARD_PATH.exists():
            return json.loads(BOARD_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return _empty()


def _write(board: dict[str, Any]) -> None:
    try:
        BOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
        board["ts"] = time.time()
        # Ограничиваем размер: последние 50 alerts / 50 tasks / 100 trail
        board["alerts"] = board.get("alerts", [])[-50:]
        board["tasks"] = board.get("tasks", [])[-50:]
        board["trail"] = board.get("trail", [])[-100:]
        BOARD_PATH.write_text(
            json.dumps(board, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


# ── Публичный API ────────────────────────────────────────

def post_alert(agent: str, level: str, text: str) -> None:
    """Агент оставляет след-тревогу. level: critical/warn/info."""
    with _LOCK:
        b = _read()
        b.setdefault("alerts", []).append({
            "agent": agent, "level": level, "text": text, "ts": time.time(),
        })
        _write(b)


def post_task(agent: str, status: str, text: str, eta: str = "") -> None:
    """Агент оставляет след-задачу."""
    with _LOCK:
        b = _read()
        b.setdefault("tasks", []).append({
            "agent": agent, "status": status, "text": text,
            "eta": eta, "ts": time.time(),
        })
        _write(b)


def set_fact(key: str, value: Any) -> None:
    """Общий факт (контекст): настроение, время, сектор."""
    with _LOCK:
        b = _read()
        b.setdefault("facts", {})[key] = value
        _write(b)


def set_sector(sector: str) -> None:
    with _LOCK:
        b = _read()
        b["sector"] = sector
        _write(b)


def log_trail(from_agent: str, to_agent: str, action: str) -> None:
    """Граф: кто кого вызвал. Основа для agent_graph."""
    with _LOCK:
        b = _read()
        b.setdefault("trail", []).append({
            "from": from_agent, "to": to_agent,
            "action": action, "ts": time.time(),
        })
        _write(b)


def snapshot() -> dict[str, Any]:
    """Полный снимок доски (для координатора)."""
    with _LOCK:
        return _read()


def recent_alerts(window_sec: float = 60.0, level: str | None = None) -> list[dict]:
    """Свежие тревоги за окно. level — фильтр."""
    now = time.time()
    b = _read()
    out = [a for a in b.get("alerts", []) if now - a["ts"] < window_sec]
    if level:
        out = [a for a in out if a["level"] == level]
    return out


def active_tasks() -> list[dict]:
    """Задачи со статусом != done."""
    b = _read()
    return [t for t in b.get("tasks", []) if t.get("status") != "done"]


def clear() -> None:
    """Очистить доску (для тестов)."""
    with _LOCK:
        _write(_empty())


__all__ = [
    "post_alert", "post_task", "set_fact", "set_sector",
    "log_trail", "snapshot", "recent_alerts", "active_tasks", "clear",
]
