"""Настройки Ауры — JSON-конфиг в ~/.config/aura/settings.json."""
from __future__ import annotations

import copy
import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".config" / "aura" / "settings.json"

DEFAULTS = {
    "wake_word": "аура",
    "wake_word_aliases": ["ара", "ура", "алло", "аула"],
    "tts_voice": "ru_RU-irina-medium",
    "tts_speed": 1.0,
    "volume": 100,
    "notifications": True,
    "proactive_enabled": True,
    "language": "ru",
    "voice_profile": "default",
    # Capability-профиль (Borderlands-style, Saltzer & Schroeder 1975):
    # elder / kid / blind / dev / admin / guest
    # Default = elder — Aura создана для elder care (MANIFESTO.md)
    "capability_profile": "elder",
    # === Elder-care опции (F-015) ===
    # Neutral defaults для обратной совместимости (раздел 20 промта).
    # Для бати эти значения переопределяются в ~/.config/aura/settings.json:
    #   "min_turn_silence": 1.8, "voice_volume_boost": 1.1,
    #   "barge_in": false, "sos_phrases": [...]
    # По науке: Saltzer & Schroeder (1975) least privilege — не навязывать.
    "min_turn_silence": 6.0,
    "vad_aggressiveness": 3,
    "voice_volume_boost": 1.0,
    "confirm_actions": False,
    "barge_in": True,
    "sos_phrases": [],  # empty = fallback на hardcoded в AgentSOS,
    # F-009: paths (нейтральные, пользователь переопределяет)
    # НЕ путать с elder-care (F-015). Здесь infra.
    "media_dirs": [],       # ["/mnt/aura_hdd/media", ...]
    "music_dirs": [],       # ["/mnt/aura_hdd/music", ...]
    "rag_db_path": "",      # "" = ~/.local/share/aura/rag_db

    "persona": {
        "name": "Аура",
        "address": "ты",
        "style": "warm",
        "humor": True,
        "voice_gender": "female",
    },
}


def load() -> dict:
    """Загрузить настройки. Недостающие — из DEFAULTS."""
    result = copy.deepcopy(DEFAULTS)
    try:
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            result.update(data)
    except Exception:
        pass
    return result


def save(settings: dict) -> None:
    """Сохранить настройки."""
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def get(key: str, default=None):
    """Получить значение."""
    return load().get(key, default)


def set_value(key: str, value) -> None:
    """Установить значение."""
    s = load()
    s[key] = value
    save(s)


def get_activation_words() -> list:
    """Все слова активации (wake_word + aliases)."""
    s = load()
    words = [s.get("wake_word", "аура")]
    words.extend(s.get("wake_word_aliases", []))
    return [w.lower() for w in words if w]


__all__ = ["load", "save", "get", "set_value", "get_activation_words",
           "DEFAULTS", "SETTINGS_PATH"]
