"""Clusters — 9 автономных кластеров агентов (Horizon GAIA).

Наука: GAIA (Horizon Zero Dawn) — 9 подфункций управляющего ИИ.
В AURA: 9 групп агентов, каждая автономна, координируется через blackboard.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Cluster:
    name: str
    purpose: str
    agents: list[str] = field(default_factory=list)


CLUSTERS: dict[str, Cluster] = {
    "health":     Cluster("health",     "Здоровье и elder-care", []),
    "voice":      Cluster("voice",      "Голос, слух, речь", []),
    "system":     Cluster("system",     "Система, окна, звук", []),
    "media":      Cluster("media",      "Медиа, музыка, видео", []),
    "info":       Cluster("info",       "Информация, погода, знания", []),
    "messengers": Cluster("messengers", "Мессенджеры, связь", []),
    "home":       Cluster("home",       "Умный дом, IoT", []),
    "infospace":  Cluster("infospace",  "Рой, координация, сектора", []),
    "self":       Cluster("self",       "Самосознание, рефлексия", []),
}


def assign_agent(agent_name: str) -> str:
    """Определить кластер по имени агента."""
    n = agent_name.lower()
    if any(k in n for k in ("sos", "fall", "med", "call", "fin", "blind", "health")):
        return "health"
    if any(k in n for k in ("voice", "speaker", "listener", "ducker", "barge")):
        return "voice"
    if any(k in n for k in ("pc", "window", "desktop", "brightness", "volume", "mouse")):
        return "system"
    if any(k in n for k in ("media", "music", "video", "vk")):
        return "media"
    if any(k in n for k in ("internet", "vault", "knowledge", "journal", "news")):
        return "info"
    if any(k in n for k in ("telegram", "whatsapp", "email", "sms", "messenger")):
        return "messengers"
    if any(k in n for k in ("mqtt", "matter", "sensor", "home", "tuya")):
        return "home"
    if any(k in n for k in ("coordinator", "sector", "scout", "miner", "blackboard")):
        return "infospace"
    if any(k in n for k in ("self", "meta", "reflect")):
        return "self"
    return "system"


def stats() -> dict[str, int]:
    """Статистика по кластерам."""
    return {name: len(c.agents) for name, c in CLUSTERS.items()}


__all__ = ["CLUSTERS", "Cluster", "assign_agent", "stats"]
