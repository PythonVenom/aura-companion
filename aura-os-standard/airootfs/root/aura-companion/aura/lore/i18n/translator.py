"""Translator — простой i18n без внешних зависимостей."""
from __future__ import annotations

from pathlib import Path

LANG_FILE = Path.home() / ".cache" / "aura" / "lang"

STRINGS: dict[str, dict[str, str]] = {
    "ru": {
        "greeting": "Доброе утро, капитан.",
        "status_ok": "Система в норме.",
        "status_bad": "Обнаружены проблемы.",
        "listening": "Слушаю.",
        "thinking": "Обрабатываю.",
    },
    "en": {
        "greeting": "Good morning, captain.",
        "status_ok": "System is nominal.",
        "status_bad": "Problems detected.",
        "listening": "Listening.",
        "thinking": "Processing.",
    },
    "hi": {
        "greeting": "सुप्रभात, कप्तान।",
        "status_ok": "सिस्टम सामान्य है।",
        "status_bad": "समस्याएँ मिलीं।",
        "listening": "सुन रही हूँ।",
        "thinking": "प्रक्रिया कर रही हूँ।",
    },
    "ta": {
        "greeting": "காலை வணக்கம், கேப்டன்.",
        "status_ok": "அமைப்பு சீராக உள்ளது.",
        "status_bad": "சிக்கல்கள் கண்டறியப்பட்டன.",
        "listening": "கேட்கிறேன்.",
        "thinking": "செயலாக்குகிறேன்.",
    },
    "ko": {
        "greeting": "좋은 아침입니다, 함장님.",
        "status_ok": "시스템 정상.",
        "status_bad": "문제가 발견되었습니다.",
        "listening": "듣고 있습니다.",
        "thinking": "처리 중입니다.",
    },
    "ja": {
        "greeting": "おはようございます、艦長。",
        "status_ok": "システムは正常です。",
        "status_bad": "問題が検出されました。",
        "listening": "聞いています。",
        "thinking": "処理中です。",
    },
    "de": {
        "greeting": "Guten Morgen, Captain.",
        "status_ok": "System ist nominal.",
        "status_bad": "Probleme erkannt.",
        "listening": "Ich höre.",
        "thinking": "Verarbeite.",
    },
}


def get_lang() -> str:
    try:
        if LANG_FILE.exists():
            return LANG_FILE.read_text().strip() or "ru"
    except Exception:
        pass
    return "ru"


def set_lang(code: str) -> bool:
    if code not in STRINGS:
        return False
    try:
        LANG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LANG_FILE.write_text(code)
        return True
    except Exception:
        return False


def translate(key: str) -> str:
    lang = get_lang()
    return STRINGS.get(lang, STRINGS["ru"]).get(key, key)


__all__ = ["STRINGS", "get_lang", "set_lang", "translate"]
