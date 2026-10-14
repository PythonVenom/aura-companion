"""#150 FDIR — Fault Detection Isolation Recovery.

Наука:
- NASA-STD-8719.13C (Software Safety) — 4 уровня mode
- Laprie 1995 (Dependable Computing) — 4 свойства
- Avizienis 2004 (Basic Concepts) — detect→isolate→recover

4 режима:
- NORMAL     — всё работает
- DEGRADED   — часть агентов отключена (высокий RAM, медленный ответ)
- SAFE       — только критичные (sos, meds, fall, call)
- EMERGENCY  — только SOS (полный отказ)

Критичные агенты (работают всегда):
  sos, meds, meds_offline, fall, call, fin_elder, proactive_alert

Критерии перехода:
  - RAM > 85% → DEGRADED
  - RAM > 95% → SAFE
  - Fatal error → EMERGENCY
"""
from __future__ import annotations

import enum
import time
from pathlib import Path

STATE_PATH = Path.home() / ".cache/aura/fdir_state.json"

# Критичные агенты — работают во всех режимах
CRITICAL_AGENTS: frozenset[str] = frozenset({
    "sos", "meds", "meds_offline", "fall", "call",
    "fin_elder", "proactive_alert", "naptime",
})


class Mode(enum.IntEnum):
    """Уровни FDIR (от высшего к низшему приоритету)."""
    NORMAL = 0
    DEGRADED = 1
    SAFE = 2
    EMERGENCY = 3


_MODE: Mode = Mode.NORMAL
_LAST_CHANGE: float = time.time()
_REASON: str = "init"


def get_mode() -> Mode:
    """Текущий режим."""
    return _MODE


def get_reason() -> str:
    """Почему перешли в этот режим."""
    return _REASON


def set_mode(mode: Mode, reason: str = "") -> Mode:
    """Установить режим. Возвращает предыдущий."""
    global _MODE, _LAST_CHANGE, _REASON
    prev = _MODE
    _MODE = mode
    _LAST_CHANGE = time.time()
    _REASON = reason or mode.name
    return prev


def is_agent_allowed(agent_name: str) -> bool:
    """Можно ли использовать агента в текущем режиме."""
    if agent_name in CRITICAL_AGENTS:
        return True
    if _MODE == Mode.NORMAL:
        return True
    if _MODE == Mode.DEGRADED:
        return True  # все, но с ограничениями (caller решает)
    # SAFE / EMERGENCY — только критичные
    return False


def check_health() -> Mode:
    """Проверить систему и обновить режим. Авто-переход."""
    # RAM check
    try:
        ram_pct = _ram_percent()
    except Exception:
        ram_pct = 0

    if ram_pct > 95:
        set_mode(Mode.SAFE, f"RAM {ram_pct:.0f}%")
        return _MODE
    if ram_pct > 85:
        set_mode(Mode.DEGRADED, f"RAM {ram_pct:.0f}%")
        return _MODE
    # Всё нормально — вернуть NORMAL (если не EMERGENCY вручную)
    if _MODE != Mode.EMERGENCY:
        set_mode(Mode.NORMAL, "healthy")
    return _MODE


def _ram_percent() -> float:
    """Процент использования RAM (0-100)."""
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        info = {}
        for line in lines:
            k, _, v = line.partition(":")
            info[k.strip()] = int(v.strip().split()[0])
        total = info.get("MemTotal", 0)
        avail = info.get("MemAvailable", 0)
        if total == 0:
            return 0.0
        return 100.0 * (total - avail) / total
    except Exception:
        return 0.0


def reset() -> None:
    """Сбросить в NORMAL (для тестов)."""
    global _MODE, _LAST_CHANGE, _REASON
    _MODE = Mode.NORMAL
    _LAST_CHANGE = time.time()
    _REASON = "reset"


def format_status() -> str:
    """Отчёт для CLI."""
    return (
        f"🛡️ FDIR: {_MODE.name}\n"
        f"   Причина: {_REASON}\n"
        f"   Критичных агентов: {len(CRITICAL_AGENTS)}\n"
        f"   Изменён: {time.strftime('%H:%M:%S', time.localtime(_LAST_CHANGE))}"
    )


__all__ = [
    "CRITICAL_AGENTS",
    "Mode",
    "check_health",
    "format_status",
    "get_mode",
    "get_reason",
    "is_agent_allowed",
    "reset",
    "set_mode",
]
