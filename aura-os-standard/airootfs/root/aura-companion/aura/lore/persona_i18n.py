"""Persona i18n — голосовые фразы AURA на 7 языках.

Наука: Multi-lingual TTS (Piper supports 30+ voices).
"""
from __future__ import annotations

from aura.lore.i18n.translator import get_lang

PHRASES: dict[str, dict[str, str]] = {
    "greeting_morning": {
        "ru": "Доброе утро, капитан.",
        "en": "Good morning, captain.",
        "hi": "सुप्रभात, कप्तान।",
        "ta": "காலை வணக்கம், கேப்டன்.",
        "ko": "좋은 아침입니다, 함장님.",
        "ja": "おはようございます、艦長。",
        "de": "Guten Morgen, Captain.",
    },
    "listening": {
        "ru": "Слушаю.",
        "en": "Listening.",
        "hi": "सुन रही हूँ।",
        "ta": "கேட்கிறேன்.",
        "ko": "듣고 있습니다.",
        "ja": "聞いています。",
        "de": "Ich höre.",
    },
    "system_ok": {
        "ru": "Система в норме.",
        "en": "System is nominal.",
        "hi": "सिस्टम सामान्य है।",
        "ta": "அமைப்பு சீராக உள்ளது.",
        "ko": "시스템 정상.",
        "ja": "システムは正常です。",
        "de": "System ist nominal.",
    },
}


def say(key: str) -> str:
    lang = get_lang()
    return PHRASES.get(key, {}).get(lang, PHRASES.get(key, {}).get("ru", key))


__all__ = ["PHRASES", "say"]
