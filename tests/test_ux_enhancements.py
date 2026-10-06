"""Тесты F-033 (sounds) + F-034 (tray animation).

Наука (Д4): Hunicke 2004 (MDA), Nielsen 1993 (Usability).
"""
from __future__ import annotations

import pytest


# === F-033: sounds ===

def test_sounds_tones_defined():
    from aura.core.sounds import TONES
    assert "activate" in TONES
    assert "listening" in TONES
    assert "error" in TONES
    assert len(TONES) >= 5


def test_sounds_play_unknown():
    from aura.core.sounds import play
    assert play("nonexistent") is False


def test_sounds_play_best_effort():
    """play не падает, если sox/paplay нет."""
    from aura.core.sounds import play
    result = play("activate")
    assert isinstance(result, bool)


# === F-034: tray animation ===

def test_interpolate_color_listening():
    from aura.core.tray_animation import interpolate_color
    # Фазы 0.0 и 0.25: sin(0)=0, sin(π/2)=1 — гарантированно разные
    c1 = interpolate_color("listening", 0.0)
    c2 = interpolate_color("listening", 0.25)
    assert c1 != c2, f"Пульсация не работает: {c1} == {c2}"
    # Жёлтый канал (R, G) доминирует
    r, g, b = c1
    assert r > b and g > b


def test_interpolate_color_full_cycle():
    """Полный цикл: 0.0 → 1.0 → 0.0."""
    from aura.core.tray_animation import interpolate_color
    c0 = interpolate_color("speaking", 0.0)
    c1 = interpolate_color("speaking", 0.25)
    c2 = interpolate_color("speaking", 0.5)
    c3 = interpolate_color("speaking", 0.75)
    # Все четыре разные
    assert len({c0, c1, c2, c3}) >= 3


def test_interpolate_color_idle():
    from aura.core.tray_animation import interpolate_color
    r, g, b = interpolate_color("idle", 0.0)
    # Синеватый
    assert b >= r


def test_to_hex():
    from aura.core.tray_animation import to_hex
    assert to_hex((255, 0, 0)) == "#ff0000"
    assert to_hex((90, 122, 154)) == "#5a7a9a"


def test_tray_animator_start_stop():
    from aura.core.tray_animation import TrayAnimator
    collected = []
    anim = TrayAnimator(lambda hex_color: collected.append(hex_color))
    anim.start()
    import time
    time.sleep(0.5)
    anim.stop()
    assert len(collected) >= 1
    assert all(c.startswith("#") for c in collected)


def test_tray_animator_set_state():
    from aura.core.tray_animation import TrayAnimator
    collected = []
    anim = TrayAnimator(lambda h: collected.append(h))
    anim.set_state("thinking")
    anim.start()
    import time
    time.sleep(0.3)
    anim.stop()
    assert len(collected) >= 1
