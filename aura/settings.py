"""Настройки Ауры — JSON-конфиг в ~/.config/aura/settings.json."""
from __future__ import annotations

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
}


def load() -> dict:
    """Загрузить настройки. Недостающие — из DEFAULTS."""
    result = dict(DEFAULTS)
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
