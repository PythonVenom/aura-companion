"""Capability-система Aura — Borderlands-style (Class + Trees + Mods + Augments).

Один движок, много билдов. Класс (base) + деревья (modifiers) + class mod
(overrides) + augment (context) → вычисленный набор прав.

Наука (Д4):
- Saltzer & Schroeder (1975). The Protection of Information in Computer Systems.
  Proc. IEEE, 63(9), 1278-1308. — least privilege
- Dennis & Van Horn (1966). Programming Semantics for Multiprogrammed Computations.
  CACM, 9(3), 143-155. — capability-based access
- Ferraiolo & Kuhn (1992). Role-Based Access Controls. NIST.
- Sandhu et al. (1996). Role-Based Access Control Models. IEEE Computer, 29(2).
  — RBAC96 с иерархией
- Hu et al. (2014). Guide to Attribute Based Access Control. NIST SP 800-162.
- Gamma et al. (1994). Design Patterns. — Composite + Decorator
- Hunicke, LeBlanc, Zubek (2004). MDA: A Formal Approach to Game Design.
  — Mechanics → Dynamics → Aesthetics (модель Borderlands)
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════
# CLASSES (base profiles) — обязательно ровно один
# ═══════════════════════════════════════════════════════════════
CLASSES: dict[str, set[str]] = {
    "elder": {
        "voice", "sos", "meds", "fall", "call", "care",
        "calendar", "music", "fin_elder", "time", "weather",
        "handsfree", "reminders",
    },
    "kid": {
        "voice", "music", "games", "education", "time",
        "parental_control", "storytelling",
    },
    "blind": {
        "voice", "tts", "screen_reader", "braille", "at_spi",
        "time", "music", "call", "navigation",
    },
    "dev": {
        "voice", "shell:safe", "git:read", "fs:read",
        "pytest", "ruff", "mcp", "text_editor", "time",
    },
    "admin": {"*"},
    "guest": {"voice", "time", "weather"},
    "auto_electric": {
        "voice", "time", "weather",
        "obd:read", "obd:clear", "obd:decode", "obd:vin",
        "can:read", "can:write", "can:decode", "can:anomaly",
        "multimeter:read", "oscilloscope:read",
        "wire_diagram:search",
        "car:history:read", "car:history:write",
        "wine:launch",
        "1c:write", "1c:read",
        "print:receipt",
    },
    "auto_mechanic": {
        "voice", "time",
        "car:history:read", "car:history:write",
        "1c:write", "1c:read",
        "print:receipt", "print:work_order",
        "parts:search", "prices:read",
    },  # demo, без persistence
}


# ═══════════════════════════════════════════════════════════════
# TREES (modifiers) — 0..N, накладываются
# ═══════════════════════════════════════════════════════════════
TREES: dict[str, set[str]] = {
    # === F-030: Veteran-specific (Borderlands trees) ===
    "ptsd": {
        # Van der Kolk (2014) — Body Keeps the Score
        "night:monitor", "trigger:detect", "calm:mode",
        "no_log", "no_history", "no_telemetry",  # приватность
    },
    "tbi": {
        # ТБИ: структура, память, когнитивная поддержка
        "structure", "reminders:strict", "cognitive:support",
    },
    "amputation": {
        # Ампутация/протез: фантомные боли, интеграция
        "phantom:track", "prosthetic:integrate",
        "voice:only", "handsfree",
    },
    "family-veteran": {
        # Для матерей/жён СВО
        "family:connect", "share:read", "reports:read",
        "sos:priority", "call:priority",
    },
    "medical": {
        "medical:read", "bpm:read", "health:read",
        "fall:notify", "meds:manage", "sos:priority",
    },
    "caregiver": {
        "family:call", "reports:read", "reports:write",
        "meds:manage", "fall:notify", "profile:read",
    },
    "family": {
        "messenger", "call", "telegram", "vk_web", "share:read",
    },
    "security": {
        "audit:read", "recon", "vault:read", "security",
        "capability:audit",
    },
    "construction": {
        "construction", "dictation", "time", "estimate",
    },
    "massage": {
        "massage", "dictation", "client:read", "client:write",
    },
    "offline": {"offline:mode", "cache:read", "no_cloud"},
    "stealth": {"no_logs", "no_history", "no_telemetry"},
    "emergency": {
        "sos", "fall", "always_on", "bypass_confirm",
        "bypass_capability_check",
    },
}


# ═══════════════════════════════════════════════════════════════
# CLASS MODS (overrides) — точечно, на конкретный билд
# ═══════════════════════════════════════════════════════════════
CLASS_MODS: dict[str, dict[str, set[str]]] = {
    # === F-030: Veteran class mods ===
    "veteran-ptsd-night": {
        # Ночь для ветерана с ПТСР
        "add": {"night_mode", "calm:priority", "no_audio_cue"},
        "disable": {"music", "sos:loud"},
    },
    "veteran-tbi-simple": {
        # ТБИ: упрощённый интерфейс
        "add": {"ui:minimal", "reminders:frequent"},
        "disable": {"multi_step_commands"},
    },
    "veteran-family": {
        # Для семьи СВО
        "add": {"family:notification", "sos:share"},
        "disable": {"psych:support"},  # только для самого ветерана
    },
    "elder-night": {
        "add": {"night_mode", "only_critical"},
        "disable": {"music_ducker", "handsfree"},
    },
    "elder-hospital": {
        "add": {"medical:read", "sos:always_on"},
        "disable": {"music", "internet"},
    },
    "dev-sandbox": {
        "add": {"shell:dry_run", "audit:log"},
        "disable": {"git:write", "fs:write"},
    },
    "kid-safe": {
        "add": {"parental_control:strict"},
        "disable": {"internet", "messenger"},
    },
}


# ═══════════════════════════════════════════════════════════════
# Profile — билд (Class + Trees + Mod + Augment)
# ═══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Profile:
    """Билд Aura."""
    name: str
    base_class: str
    trees: tuple[str, ...] = ()
    class_mod: str | None = None
    augment: dict = field(default_factory=dict)
    platform: str = "auto"

    def capabilities(self) -> frozenset[str]:
        """Вычислить итоговый набор прав (Composite + Decorator)."""
        caps: set[str] = set(CLASSES.get(self.base_class, set()))
        for t in self.trees:
            caps |= TREES.get(t, set())
        if self.class_mod:
            mod = CLASS_MODS.get(self.class_mod, {})
            caps |= mod.get("add", set())
            caps -= mod.get("disable", set())
        return frozenset(caps)

    def has(self, capability: str) -> bool:
        """Проверить одно право. `*` — wildcard (admin)."""
        caps = self.capabilities()
        return "*" in caps or capability in caps


# ═══════════════════════════════════════════════════════════════
# Runtime state — единый «текущий билд» для процесса
# ═══════════════════════════════════════════════════════════════
_CURRENT: Profile | None = None


def set_current(profile: Profile | None) -> None:
    """Установить активный профиль (обычно при старте)."""
    global _CURRENT
    _CURRENT = profile


def current() -> Profile | None:
    """Текущий активный профиль."""
    return _CURRENT


def require(capability: str) -> bool:
    """Проверить, разрешена ли операция для текущего профиля.

    Возвращает False, если профиль не установлен (fail-closed,
    Saltzer & Schroeder 1975: default-deny).
    """
    if _CURRENT is None:
        return False
    return _CURRENT.has(capability)


# ═══════════════════════════════════════════════════════════════
# AGENT → CAPABILITY mapping (централизованно)
# ═══════════════════════════════════════════════════════════════
# Агент, отсутствующий в карте — fail-open с warning
# (раздел 20 промта: постепенный переход, не сломать elder-care).
#
# Через 2-3 итерации все агенты должны быть в карте → fail-closed.
AGENT_CAPABILITIES: dict[str, str] = {
    # elder-care core
    "sos": "sos",
    "meds": "meds",
    "fall": "fall",
    "call": "call",
    "care": "care",
    "fin_elder": "fin_elder",
    "reminders": "reminders",
    # voice / TTS
    "voice": "voice",
    "speaker": "voice",
    "listener": "voice",
    "barge_in": "voice",
    "handsfree": "handsfree",
    # music / media
    "music_local": "music",
    "music_ducker": "music",
    "media_pause": "music",
    "media_search": "music",
    "media_state": "music",
    # time / weather
    "time": "time",
    "time_agent": "time",
    "weather": "weather",
    # calendar / notes
    "calendar": "calendar",
    "checklist": "calendar",
    "text_editor": "text_editor",
    # security / vault
    "vault": "vault:read",
    "security": "security",
    "recon": "recon",
    # dev (для будущих)
    "shell": "shell:safe",
    "git": "git:read",
    "ruff": "ruff",
    "pytest": "pytest",
    "mcp": "mcp",
    # medical (trees)
    "bpm": "bpm:read",
    "health": "health:read",
    "health_twin": "health:read",
    # messenger / social
    "messenger": "messenger",
    "telegram": "telegram",
    "vk_web": "vk_web",
    # construction / massage
    "construction": "construction",
    "massage": "massage",
    "dictation": "dictation",
    "onboarding": "onboarding:setup",
    "tutorial": "tutorial:learn",
    "self_check": "self:check",
    # === F-030: Veteran-specific ===
    "reminiscence": "reminiscence",  # уже есть в elder
    "emotion_voice": "psych:support",
    "sleep_monitor": "sleep:monitor",  # TODO: новый агент
    "phantom_tracker": "phantom:track",  # TODO
}


__all__ = [
    "AGENT_CAPABILITIES",
    "CLASSES",
    "CLASS_MODS",
    "TREES",
    "Profile",
    "current",
    "require",
    "set_current",
]
