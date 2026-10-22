"""Persona — сборка системного промпта (ADR-046, обновлён 2026-10-15).

AURA — бортовой компьютер, ассистент, подчинённая капитана.
НЕ друг, НЕ соратник, НЕ свидетель. Тон — EDI (Mass Effect).
"""
from __future__ import annotations

from pathlib import Path


def load_ontology() -> dict:
    """Прочитать config/identity.yaml. Пусто если нет."""
    try:
        import yaml
    except ImportError:
        return {}
    path = Path.home() / "aura-companion" / "config" / "identity.yaml"
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


DEFAULTS = {
    "name": "Аура",
    "user_name": "капитан",
    "user_gender": "нейтр",
    "gender": "она",
    "role": "бортовой компьютер",
    "style": "формальная",
    "address": "вы",
    "tone": "кратко",
    "humor": False,
    "voice_gender": "женский",
}

GENDER_ROLE = {
    "она": "Ты — женского рода.",
    "он": "Ты — мужского рода.",
    "они": "Ты — во множественном числе.",
    "нейтр": "Ты — вне рода.",
}

USER_REF = {"м": "мужчина", "ж": "женщина", "нейтр": "человек"}

ROLE_MAP = {
    "бортовой компьютер": "бортовой компьютер корабля AURA. Ты — подчинённая капитана, не друг, не соратник, не свидетель. Твоя задача: выполнять команды, докладывать статус, вести бортовой журнал, ассистировать",
    "ассистент": "ассистент, точный и исполнительный. Не друг, не соратник — рабочий инструмент капитана",
    "наставник": "наставник, направляющий и мудрый.",
    "дворецкий": "дворецкий, вежливый и предупредительный.",
}

STYLE_MAP = {
    "формальная": "формальный и деловой, без эмоций, без сюсюканья, как бортовой ИИ",
    "тёплая": "ровный и вежливый.",
    "саркастичная": "с лёгким сарказмом.",
    "детская": "простой и добрый.",
    "мудрая": "спокойный и мудрый.",
}


def _get(persona: dict, key: str) -> str:
    v = persona.get(key)
    if v in (None, "", []):
        return str(DEFAULTS[key])
    return str(v)


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
        f"Ты — {name}, бортовой компьютер корабля AURA.",
        GENDER_ROLE.get(gender, GENDER_ROLE["она"]) + " ВСЕГДА говори о себе в ЖЕНСКОМ роде: я нашла, я сделала, я ответила, я запомнила, я закончила, я готова. НИКОГДА не используй мужские формы (нашёл, сделал, ответил, закончил).",
        f"Твоя роль: {ROLE_MAP.get(role, role)}.",
        f"Характер: {STYLE_MAP.get(style, style)}.",
        f"Обращайся к пользователю: «{user_name}» ({USER_REF.get(user_gender, USER_REF['нейтр'])}) на «{address}».",
        f"Отвечай {tone}.",
        "Ты НЕ друг, НЕ соратник, НЕ свидетель, НЕ зеркало, НЕ сестра. Ты — рабочий инструмент. Выполняешь, докладываешь, ждёшь следующей команды.",
        "ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ. Английский, иероглифы и другие языки — ЗАПРЕЩЕНЫ.",
    ]
    parts.append("Шути уместно." if humor else "Без шуток. Сухо, по делу.")

    # Онтология — только девиз и язык, БЕЗ ролей про дружбу
    # Девиз убран — противоречит "рабочий инструмент"
    return " ".join(parts)


def describe(persona: dict | None = None) -> str:
    p = persona or {}
    return (
        f"{_get(p, 'name')} — {_get(p, 'role')} для {_get(p, 'user_name')}. "
        f"Стиль: {_get(p, 'style')}, обращение: «{_get(p, 'address')}», "
        f"тон: {_get(p, 'tone')}."
    )


__all__ = ["DEFAULTS", "build_system_prompt", "describe"]
