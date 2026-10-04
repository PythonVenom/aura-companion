"""Capability Graph — карта возможностей Aura (ADR-101).

Каждый узел = действие с входами/выходами.
Используется HTN Planner + ReAct Loop.

YAGNI: 30-50 узлов = 80% покрытия. Не описывать все 44 агента.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Capability:
    name: str                       # "music.play"
    description: str                # "включить музыку"
    inputs: list = field(default_factory=list)   # ["query"]
    outputs: list = field(default_factory=list)  # ["bool"]
    tags: list = field(default_factory=list)     # ["media", "safe"]
    handler: Optional[Callable] = None


class CapabilityGraph:
    def __init__(self):
        self.nodes: dict = {}

    def add(self, cap: Capability):
        self.nodes[cap.name] = cap

    def get(self, name: str) -> Optional[Capability]:
        return self.nodes.get(name)

    def by_tag(self, tag: str) -> list:
        return [c for c in self.nodes.values() if tag in c.tags]

    def all_names(self) -> list:
        return sorted(self.nodes.keys())

    def find_for(self, verb: str) -> list:
        return [c for c in self.nodes.values() if verb in c.name]


def build_default_graph() -> CapabilityGraph:
    g = CapabilityGraph()
    # CORE
    g.add(Capability("time.now", "текущее время", [], ["str"], ["core"]))
    g.add(Capability("time.date", "текущая дата", [], ["str"], ["core"]))
    # MEDIA
    g.add(Capability("music.play", "включить музыку", ["query"], ["bool"], ["media"]))
    g.add(Capability("music.pause", "пауза", [], ["bool"], ["media"]))
    g.add(Capability("music.next", "следующий трек", [], ["bool"], ["media"]))
    g.add(Capability("music.prev", "предыдущий трек", [], ["bool"], ["media"]))
    # WINDOWS
    g.add(Capability("window.focus", "фокус на окно", ["name"], ["bool"], ["de"]))
    g.add(Capability("window.list", "список окон", [], ["list"], ["de"]))
    g.add(Capability("window.close", "закрыть окно", ["name"], ["bool"], ["de", "danger"]))
    # APP
    g.add(Capability("app.launch", "запустить приложение", ["name"], ["bool"], ["de"]))
    # BROWSER
    g.add(Capability("browser.open", "открыть URL", ["url"], ["bool"], ["web"]))
    g.add(Capability("browser.tab_list", "вкладки", [], ["list"], ["web"]))
    g.add(Capability("browser.find_tab", "найти вкладку", ["query"], ["tab"], ["web"]))
    # VK
    g.add(Capability("vk.navigate", "раздел VK", ["section"], ["bool"], ["web"]))
    g.add(Capability("vk.send_message", "отправить сообщение", ["text"], ["bool"], ["web"]))
    g.add(Capability("vk.list_chats", "список чатов", [], ["list"], ["web"]))
    # CARE (v2.5)
    g.add(Capability("care.list", "список напоминаний", [], ["list"], ["care"]))
    g.add(Capability("care.add", "добавить напоминание", ["name", "times", "msg"], ["bool"], ["care"]))
    # JOURNAL
    g.add(Capability("journal.add", "запись настроения", ["text", "mood"], ["bool"], ["journal"]))
    g.add(Capability("journal.stats", "статистика настроения", ["days"], ["dict"], ["journal"]))
    # FOCUS
    g.add(Capability("focus.enable", "режим фокуса", ["minutes"], ["bool"], ["care"]))
    g.add(Capability("focus.disable", "выключить фокус", [], ["bool"], ["care"]))
    # HANDS-FREE
    g.add(Capability("handsfree.on", "слушать без активации", ["seconds"], ["bool"], ["care"]))
    g.add(Capability("handsfree.off", "выключить hands-free", [], ["bool"], ["care"]))
    # CONTEXT
    g.add(Capability("context.recent", "что делал", ["minutes"], ["str"], ["meta"]))
    # RECON
    g.add(Capability("recon.run", "диагностика", [], ["str"], ["meta"]))
    # WORLD
    g.add(Capability("world.state", "состояние системы", [], ["str"], ["meta"]))
    # CONTROL (aura_ctl)
    g.add(Capability("control.pause", "пауза Aura", [], ["bool"], ["control"]))
    g.add(Capability("control.resume", "продолжить", [], ["bool"], ["control"]))
    g.add(Capability("control.restart", "рестарт", [], ["bool"], ["control", "danger"]))
    g.add(Capability("control.kill", "kill Aura", [], ["bool"], ["control", "danger"]))
    # POWER
    g.add(Capability("power.lock", "заблокировать экран", [], ["bool"], ["power"]))
    g.add(Capability("power.shutdown", "выключить ПК", [], ["bool"], ["power", "danger"]))
    return g


_graph = None
def get_graph() -> CapabilityGraph:
    global _graph
    if _graph is None:
        _graph = build_default_graph()
    return _graph


__all__ = ["Capability", "CapabilityGraph", "build_default_graph", "get_graph"]
