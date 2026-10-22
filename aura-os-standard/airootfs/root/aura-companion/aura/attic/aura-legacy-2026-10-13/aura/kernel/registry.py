"""Registry — кто жив в организме."""
import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("aura.registry")


@dataclass
class Organ:
    name: str
    process: Any = None
    status: str = "init"
    restarts: int = 0
    meta: dict = field(default_factory=dict)


class Registry:
    def __init__(self):
        self._organs: dict[str, Organ] = {}

    def register(self, name: str, process=None, **meta) -> Organ:
        organ = Organ(name=name, process=process, status="running", meta=meta)
        self._organs[name] = organ
        log.info("register: %s (%s)", name, meta)
        return organ

    def unregister(self, name: str):
        self._organs.pop(name, None)

    def get(self, name: str) -> Organ | None:
        return self._organs.get(name)

    def alive(self) -> list[str]:
        return [n for n, o in self._organs.items() if o.status == "running"]

    def dead(self) -> list[str]:
        return [n for n, o in self._organs.items() if o.status != "running"]

    def all(self) -> dict:
        return {n: o.status for n, o in self._organs.items()}


registry = Registry()
