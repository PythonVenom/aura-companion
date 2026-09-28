"""Voice Profiles — стили общения (ADR-040)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceProfile:
    name: str
    rate: float = 1.0
    style: str = "warm"
    vocab: str = "default"
    description: str = ""


PROFILES: dict[str, VoiceProfile] = {
    "default": VoiceProfile("default", 1.0, "warm", "default", "дом, офис"),
    "medical": VoiceProfile("medical", 1.1, "neutral", "medical", "клиника"),
    "craft": VoiceProfile("craft", 0.95, "neutral", "technical", "мастерская"),
    "drive": VoiceProfile("drive", 1.2, "brief", "short", "за рулём"),
    "kids": VoiceProfile("kids", 0.85, "gentle", "simple", "дети"),
    "dev": VoiceProfile("dev", 1.0, "technical", "it", "программирование"),
    "accessibility": VoiceProfile("accessibility", 0.9, "patient", "verbose", "бабушка"),
}


def get_profile(name: str) -> VoiceProfile:
    """Получить профиль по имени. Fallback — default."""
    return PROFILES.get(name, PROFILES["default"])


def list_profiles() -> list[VoiceProfile]:
    return list(PROFILES.values())


def apply_to_persona(profile_name: str, persona: dict) -> dict:
    """Применить профиль к persona (для speaker)."""
    p = get_profile(profile_name)
    result = dict(persona)
    result["style"] = p.style
    result["rate"] = p.rate
    result["vocab"] = p.vocab
    return result


__all__ = ["VoiceProfile", "PROFILES", "get_profile", "list_profiles", "apply_to_persona"]
