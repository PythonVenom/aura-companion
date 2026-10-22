"""Aura Capability Security."""
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    granted_to: str
    expires_at: float


class CapabilityRegistry:
    def __init__(self):
        self._caps: dict[str, list[Capability]] = {}

    def grant(self, agent: str, name: str, ttl: float = 0) -> Capability:
        expires = time.time() + ttl if ttl > 0 else 0
        cap = Capability(name=name, granted_to=agent, expires_at=expires)
        self._caps.setdefault(agent, []).append(cap)
        return cap

    def can(self, agent: str, name: str) -> bool:
        now = time.time()
        for cap in self._caps.get(agent, []):
            if cap.name == name and (cap.expires_at == 0 or cap.expires_at > now):
                return True
        return False

    def list_for(self, agent: str) -> list[str]:
        return [c.name for c in self._caps.get(agent, [])]


capabilities = CapabilityRegistry()
