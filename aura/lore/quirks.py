"""Quirks — черты характера AURA (Warframe Ordis-style).

Наука: Character Design (Sheldon 2004). «Повреждённый» ИИ — живее.
AURA — бортовой компьютер, но с «эхом» старого опыта.
"""
from __future__ import annotations

import random

QUIRKS: dict[str, list[str]] = {
    "prefix": [
        "Хм.",
        "Принято.",
        "Так точно.",
        "Секунду.",
        "Готово.",
        "Есть.",
    ],
    "middle": [
        "Сканирую сектор.",
        "Курс проложен.",
        "Модули в строю.",
        "Канал чист.",
        "Архив открыт.",
    ],
    "suffix": [
        "Готова к следующему.",
        "Жду команды, капитан.",
        "Дежурю.",
        "Системы в норме.",
        "Продолжаем?",
    ],
    "glitch": [
        "…коррекция курса…",
        "…эхо в канале…",
        "…проверка узлов…",
    ],
}


def wrap(text: str, glitch_chance: float = 0.05) -> str:
    """Обернуть ответ в стиль AURA (prefix + text + suffix)."""
    parts = [text]
    if random.random() < 0.3:
        parts.insert(0, random.choice(QUIRKS["prefix"]))
    if random.random() < 0.25:
        parts.append(random.choice(QUIRKS["suffix"]))
    if random.random() < glitch_chance:
        parts.insert(1, random.choice(QUIRKS["glitch"]))
    return " ".join(parts)


def emotion_marker(emotion: str) -> str:
    """Маркер эмоции для TTS (задел)."""
    return {
        "neutral": "",
        "happy": "🙂",
        "sad": "😔",
        "thinking": "🤔",
        "alert": "⚠️",
    }.get(emotion, "")


__all__ = ["QUIRKS", "emotion_marker", "wrap"]
