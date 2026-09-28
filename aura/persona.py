"""Persona — сборка системного промпта из онбординг-анкеты (ADR-046).

Pure-функции без побочек: dict persona → строка промпта.
"""
from __future__ import annotations

# Дефолты — если поле пустое
DEFAULTS = {
    "name": "Аура",
    "user_name": "друг",
    "user_gender": "нейтр",
    "gender": "она",
    "role": "друг",
    "style": "тёплая",
    "address": "ты",
    "tone": "кратко",
    "humor": True,
    "voice_gender": "женский",
}

# Маппинги: код → человекочитаемое
GENDER_ROLE = {
    "она": "Ты — женского рода.",
    "он": "Ты — мужского рода.",
    "они": "Ты — во множественном числе (they/them).",
    "нейтр": "Ты — вне рода (не склоняйся по полу).",
}

USER_REF = {
    "м": "мужчина",
    "ж": "женщина",
    "нейтр": "человек",
}

ROLE_MAP = {
    "ассистент": "помощник, чёткий и полезный",
    "друг": "близкий друг, поддерживающий и честный",
    "наставник": "наставник, направляющий и мудрый",
    "муза": "муза, вдохновляющая и креативная",
    "дворецкий": "дворецкий, вежливый и предупредительный",
    "свой": "ассистент с индивидуальностью",
}

STYLE_MAP = {
    "тёплая": "тёплый и заботливый",
    "саркастичная": "с лёгким сарказмом и иронией",
    "формальная": "формальный и деловой",
    "детская": "простой и добрый, как для ребёнка",
    "мудрая": "спокойный и мудрый",
}


def _get(persona: dict, key: str) -> str:
    v = persona.get(key)
    if v in (None, "", []):
        return DEFAULTS[key]
    return v


def build_system_prompt(persona: dict | None = None) -> str:
    """Собрать системный промпт для LLM из persona-словаря."""
    p = persona or {}
    name = _get(p, "name")
    user_name = _get(p, "user_name")
    user_gender = _get(p, "user_gender")
    gender = _get(p, "gender")
    role = _get(p, "role")
    style = _get(p, "style")
    address = _get(p, "address")
    tone = _get(p, "tone")
    humor = p.get("humor", DEFAULTS["humor"])

    parts = [
        f"Ты — {name}.",
        GENDER_ROLE.get(gender, GENDER_ROLE["она"]),
        f"Твоя роль: {ROLE_MAP.get(role, role)}.",
        f"Характер: {STYLE_MAP.get(style, style)}.",
        f"Обращайся к пользователю по имени «{user_name}» "
        f"({USER_REF.get(user_gender, USER_REF['нейтр'])}) на «{address}».",
        f"Отвечай {tone}.",
    ]
    parts.append("Шути уместно." if humor else "Без шуток.")
    return " ".join(parts)


def describe(persona: dict | None = None) -> str:
    """Короткое человекочитаемое описание (для вывода после онбординга)."""
    p = persona or {}
    return (
        f"{_get(p, 'name')} — {_get(p, 'role')} для {_get(p, 'user_name')}. "
        f"Стиль: {_get(p, 'style')}, обращение: «{_get(p, 'address')}», "
        f"тон: {_get(p, 'tone')}."
    )


__all__ = ["DEFAULTS", "build_system_prompt", "describe"]
