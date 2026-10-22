"""Универсальный доступ к payload. Работает и с Event, и с dict.
Наука: Adapter Pattern. Один интерфейс — разные входы.
"""
from typing import Any


def get_payload(event: Any) -> dict[str, Any]:
    """Достать payload из Event или dict."""
    if hasattr(event, "payload"):
        return event.payload or {}
    if isinstance(event, dict):
        return event
    return {}
