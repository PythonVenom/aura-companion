"""Bug 33 — распознавание команды «стоп/тише/хватит» во время речи Aura.

Наука:
- ITU-T G.168 — Acoustic Echo Control (MIN_RMS в barge_in)
- Keyword Spotting (Warden 2018) — короткие команды в потоке
- Nielsen #3 — User Control and Freedom (юзер может прервать)

Проблема:
  Пока Aura говорит — не слышит «Аура стоп». barge_in VAD
  ловит факт речи, но не распознаёт слова.

Решение:
  barge_in.on_speech → короткое окно (1.5с) → Vosk → матч STOP_WORDS.
  Если «стоп/тише/хватит» → speaker.stop_speaking().

Почему Vosk:
- Уже в проекте (blind_reply.py)
- Offline, RU, быстрый
- Не требует API
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# Ключевые слова прерывания (RU)
STOP_WORDS: tuple[str, ...] = (
    "стоп",
    "тише",
    "хватит",
    "замолчи",
    "прекрати",
    "заткнись",
    "тихо",
    "молчи",
    "пауза",
    "стой",
)

# Vosk модели (как в blind_reply.py)
VOSK_PATHS = [
    Path.home() / ".cache/vosk/vosk-model-small-ru",
    Path("/usr/share/vosk/vosk-model-small-ru"),
    Path.home() / ".local/share/vosk/vosk-model-small-ru",
]


def find_vosk_model() -> str | None:
    """Найти Vosk-модель."""
    for p in VOSK_PATHS:
        if p.is_dir():
            return str(p)
    return None


def is_stop(text: str) -> bool:
    """True если в тексте есть стоп-слово."""
    if not text:
        return False
    t = text.lower().strip()
    # Нормализация: убираем пунктуацию
    t = re.sub(r"[^\w\s]", " ", t)
    words = t.split()
    return any(word in STOP_WORDS for word in words)


def recognize_stop(frames_pcm16: bytes, sample_rate: int = 16000) -> bool:
    """Распознать фреймы через Vosk → матч STOP_WORDS.

    frames_pcm16: сырые int16 PCM (mono).
    Возвращает True если в речи есть стоп-слово.
    """
    try:
        import vosk
    except ImportError:
        return False

    model_path = find_vosk_model()
    if not model_path:
        return False

    try:
        rec = vosk.KaldiRecognizer(vosk.Model(model_path), sample_rate)
        rec.AcceptWaveform(frames_pcm16)
        result = rec.FinalResult()
        import json
        text = json.loads(result).get("text", "")
        return is_stop(text)
    except Exception:
        return False


__all__ = ["is_stop", "recognize_stop", "find_vosk_model", "STOP_WORDS"]
