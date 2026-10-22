"""AgentGraph — граф связей между 108 агентами (следующий уровень роя).

Наука:
- Graph Neural Networks (Scarselli 2009, Kipf 2017)
- Multi-Agent RL with Graph Attention (Veličković 2018)
- Stigmergy trail → weighted directed graph

Идея: trail из blackboard — это рёбра графа. Вес ребра = частота вызовов.
Граф позволяет:
- видеть «кластеры» агентов (elder-care, media, system),
- распространять сигналы (alert от fall → boost sos/meds),
- выявлять «мёртвые» рёбра (агенты, которые не зовут друг друга).

Лёгкая реализация без PyTorch Geometric — обычный networkx-style dict.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from aura.core import blackboard as bb


@dataclass
class AgentGraph:
    """Граф роя: узлы = агенты, рёбра = trail из blackboard."""

    nodes: set[str] = field(default_factory=set)
    edges: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    actions: dict[tuple[str, str], str] = field(default_factory=dict)
    last_build: float = 0.0

    def build_from_blackboard(self) -> None:
        """Собрать граф из trail на доске."""
        snap = bb.snapshot()
        trail = snap.get("trail", [])
        self.nodes.clear()
        self.edges.clear()
        self.actions.clear()
        for t in trail:
            f, to = t.get("from"), t.get("to")
            if not f or not to:
                continue
            self.nodes.add(f)
            self.nodes.add(to)
            key = (f, to)
            self.edges[key] += 1
            self.actions[key] = t.get("action", "")
        self.last_build = time.time()

    def neighbors(self, agent: str) -> dict[str, int]:
        """Соседи узла с весами (кто зовёт / кого зовёт)."""
        out: dict[str, int] = {}
        for (f, to), w in self.edges.items():
            if f == agent:
                out[to] = out.get(to, 0) + w
            elif to == agent:
                out[f] = out.get(f, 0) + w
        return out

    def propagate_alert(self, source: str, depth: int = 2) -> dict[str, float]:
        """Распространить сигнал от источника по графу (BFS с затуханием).

        Возвращает {agent: weight} — кого бустить при тревоге.
        """
        weights: dict[str, float] = {source: 1.0}
        frontier = {source: 1.0}
        for _ in range(depth):
            next_frontier: dict[str, float] = {}
            for node, w in frontier.items():
                for nb, edge_w in self.neighbors(node).items():
                    new_w = w * 0.5 * min(edge_w, 3)  # затухание + вес
                    if new_w > weights.get(nb, 0):
                        weights[nb] = new_w
                        next_frontier[nb] = new_w
            frontier = next_frontier
        return weights

    def clusters(self) -> dict[str, list[str]]:
        """Простые кластеры по префиксу имени агента."""
        clusters: dict[str, list[str]] = defaultdict(list)
        for n in sorted(self.nodes):
            # elder-care = fall/sos/meds/call/fin_elder/blind
            if n in {"fall", "sos", "meds", "call", "fin_elder", "blind",
                     "blind_reply", "sms", "emotion_voice", "soul_talk"}:
                clusters["elder-care"].append(n)
            elif n.startswith("media") or n in {"music_ducker", "music_local"}:
                clusters["media"].append(n)
            elif "coordinator" in n or "sector" in n or "scout" in n or "miner" in n:
                clusters["infospace"].append(n)
            else:
                clusters["other"].append(n)
        return dict(clusters)

    def stats(self) -> dict[str, Any]:
        if not self.last_build:
            self.build_from_blackboard()
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "top_edges": sorted(
                ((f, t, w) for (f, t), w in self.edges.items()),
                key=lambda x: -x[2],
            )[:5],
            "clusters": {k: len(v) for k, v in self.clusters().items()},
            "last_build": self.last_build,
        }


def get_graph() -> AgentGraph:
    """Свежий граф из blackboard."""
    g = AgentGraph()
    g.build_from_blackboard()
    return g


__all__ = ["AgentGraph", "get_graph"]
