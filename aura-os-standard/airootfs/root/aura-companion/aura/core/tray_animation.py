"""Tray pulsing animation (F-034).

Пульсация иконки трея в зависимости от state:
- listening → жёлтая пульсация
- thinking  → оранжевая
- speaking  → зелёная пульсация
- idle      → синий статичный

Наука: Nielsen 1993 (Visibility of system status),
       Hunicke 2004 (MDA — feedback).
"""
from __future__ import annotations

import math
import threading
import time

STATE_COLORS_ANIM = {
    "idle":      (90, 122, 154),
    "listening": (245, 197, 66),
    "thinking":  (245, 135, 66),
    "speaking":  (66, 197, 90),
    "paused":    (102, 102, 102),
    "error":     (197, 66, 66),
}


def interpolate_color(state: str, phase: float) -> tuple:
    """Пульсация: цвет ± 20% яркости."""
    base = STATE_COLORS_ANIM.get(state, STATE_COLORS_ANIM["idle"])
    # phase 0..1 → 0.8..1.0
    factor = 0.8 + 0.2 * (0.5 + 0.5 * math.sin(phase * 2 * math.pi))
    return tuple(min(255, int(c * factor)) for c in base)


def to_hex(rgb: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


class TrayAnimator:
    """Аниматор для tray-иконки (threading).

    Использование:
        anim = TrayAnimator(update_callback)
        anim.set_state("listening")
        anim.start()
        ...
        anim.stop()
    """

    def __init__(self, update_callback, fps: int = 4):
        self._update = update_callback
        self._fps = fps
        self._state = "idle"
        self._running = False
        self._thread: threading.Thread | None = None

    def set_state(self, state: str) -> None:
        self._state = state

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        phase = 0.0
        interval = 1.0 / self._fps
        while self._running:
            try:
                rgb = interpolate_color(self._state, phase)
                self._update(to_hex(rgb))
                phase = (phase + 0.1) % 1.0
            except Exception:
                pass
            time.sleep(interval)


__all__ = ["STATE_COLORS_ANIM", "TrayAnimator", "interpolate_color", "to_hex"]
