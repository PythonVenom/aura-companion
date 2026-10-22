"""Aura UX Sounds (F-033).

Мягкие звуки интерфейса — не речевые, не громкие.
Наука: Hunicke 2004 (MDA — Aesthetics через звук),
       Nielsen 1993 (Usability — audio feedback).

Использование:
    from aura.core.sounds import play
    play("activate")   # при wake word
    play("thinking")   # когда думает
    play("error")      # при ошибке
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger("aura.sounds")

# Fallback: генерим через sox/ffmpeg, если нет готовых wav.
SOUNDS_DIR = Path.home() / ".local" / "share" / "aura" / "sounds"

# Описание (частота, длительность, тип) — генерим через sox
TONES = {
    "activate":   {"freq": 880, "dur": 0.08, "type": "sine"},
    "listening":  {"freq": 660, "dur": 0.05, "type": "sine"},
    "thinking":   {"freq": 440, "dur": 0.10, "type": "sine"},
    "success":    {"freq": 1320, "dur": 0.15, "type": "sine"},
    "error":      {"freq": 220, "dur": 0.20, "type": "sine"},
    "pause":      {"freq": 330, "dur": 0.15, "type": "sine"},
}


def _ensure_sounds() -> bool:
    """Генерит wav через sox, если нет."""
    if not shutil.which("sox"):
        return False
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    for name, spec in TONES.items():
        wav = SOUNDS_DIR / f"{name}.wav"
        if wav.exists():
            continue
        try:
            subprocess.run(
                ["sox", "-n", str(wav),
                 "synth", str(spec["dur"]),
                 spec["type"], str(spec["freq"]),
                 "fade", "q", "0.02", str(spec["dur"]), "0.02",
                 "vol", "0.3"],
                check=True, timeout=5,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            log.debug("sox gen %s failed: %s", name, e)
    return True


def play(name: str) -> bool:
    """Проиграть звук. Best-effort, не блокирует."""
    if name not in TONES:
        return False
    _ensure_sounds()
    wav = SOUNDS_DIR / f"{name}.wav"
    if not wav.exists():
        return False
    # paplay (PipeWire/Pulse), потом aplay (ALSA)
    for player in ("paplay", "aplay", "pw-play"):
        if shutil.which(player):
            try:
                subprocess.Popen(
                    [player, str(wav)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception:
                continue
    return False


__all__ = ["SOUNDS_DIR", "TONES", "play"]
