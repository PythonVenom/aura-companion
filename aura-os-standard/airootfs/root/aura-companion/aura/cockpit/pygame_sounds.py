"""F-094e: звуки pygame — программные, без WAV-файлов.

Генерируются через numpy → pygame.mixer.Sound.
- click  — 800 Hz, 50 ms
- shot   — 220 Hz, 100 ms
- hit    — 400 Hz, 80 ms
- win    — 880 Hz, 200 ms
- lose   — 150 Hz, 300 ms
- advisor — 600 Hz, 150 ms
"""
from __future__ import annotations

import math
import struct

import pygame

SAMPLE_RATE = 22050


def _square(freq: float, duration: float, volume: float = 0.3) -> bytes:
    """Сгенерировать square wave. Возвращает raw PCM bytes (16-bit, mono)."""
    n = int(SAMPLE_RATE * duration)
    amp = int(32767 * volume)
    half = SAMPLE_RATE / freq / 2
    out = bytearray()
    for i in range(n):
        # envelope: fade in/out 5 ms
        env = 1.0
        ms = SAMPLE_RATE / 1000.0
        if i < 5 * ms:
            env = i / (5 * ms)
        elif i > n - 5 * ms:
            env = (n - i) / (5 * ms)
        v = amp if (i % (half * 2)) < half else -amp
        v = int(v * env)
        out += struct.pack("<h", v)
    return bytes(out)


def _sine(freq: float, duration: float, volume: float = 0.3) -> bytes:
    """Синусоида — мягче для мелодий."""
    n = int(SAMPLE_RATE * duration)
    amp = int(32767 * volume)
    out = bytearray()
    ms = SAMPLE_RATE / 1000.0
    for i in range(n):
        env = 1.0
        if i < 5 * ms:
            env = i / (5 * ms)
        elif i > n - 5 * ms:
            env = (n - i) / (5 * ms)
        v = int(amp * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) * env)
        out += struct.pack("<h", v)
    return bytes(out)


class Sounds:
    """Звуковой менеджер. Один на процесс."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._lib: dict[str, pygame.mixer.Sound] = {}
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            self._lib = {
                "click":   pygame.mixer.Sound(buffer=_square(800, 0.05, 0.20)),
                "shot":    pygame.mixer.Sound(buffer=_square(220, 0.10, 0.25)),
                "hit":     pygame.mixer.Sound(buffer=_square(400, 0.08, 0.25)),
                "win":     pygame.mixer.Sound(buffer=_sine(880, 0.20, 0.30)),
                "lose":    pygame.mixer.Sound(buffer=_square(150, 0.30, 0.25)),
                "advisor": pygame.mixer.Sound(buffer=_sine(600, 0.15, 0.20)),
                "jump":    pygame.mixer.Sound(buffer=_sine(1200, 0.12, 0.20)),
            }
        except Exception as e:
            print(f"⚠️ Sounds init: {e}")
            self.enabled = False

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        snd = self._lib.get(name)
        if snd is not None:
            snd.play()
