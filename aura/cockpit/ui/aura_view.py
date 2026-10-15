"""AURA View — UI от лица AURA (Observation game-style).

Наука: Observation (2019), диегетический UI.
Капитан видит мир глазами AURA: сектор, агенты, память.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuraView:
    """Снимок состояния от лица AURA."""
    sector: str = "unknown"
    agents: int = 0
    alerts: int = 0
    tasks: int = 0
    emotion: str = "calm"
    online: bool = True


def snapshot() -> AuraView:
    """Собрать снимок."""
    v = AuraView()
    try:
        from aura.core import blackboard as bb
        snap = bb.snapshot()
        v.sector = snap.get("sector", "unknown")
        v.alerts = len(bb.recent_alerts(window_sec=300))
        v.tasks = len(bb.active_tasks())
    except Exception:
        pass
    try:
        from aura.bootstrap import build_orchestrator
        v.agents = len(build_orchestrator())
    except Exception:
        pass
    try:
        from aura.core.emotion_evolution import get_state
        v.emotion = get_state().dominant()
    except Exception:
        pass
    try:
        from aura.indicators import is_online
        v.online = is_online()
    except Exception:
        pass
    return v


def render(v: AuraView | None = None) -> str:
    """Отрисовать вид от первого лица."""
    v = v or snapshot()
    net = "🟢" if v.online else "⚫"
    return f"""
╔══════════════════════════════════════════════════════════════╗
║  🛸 AURA // БОРТОВОЙ ВИД                                     ║
║  {net} Сектор: {v.sector:<12s} | Эмоция: {v.emotion:<10s}              ║
╠══════════════════════════════════════════════════════════════╣
║  Экипаж (агенты): {v.agents:>4d}     Активных задач: {v.tasks:>2d}            ║
║  Тревог (5 мин):  {v.alerts:>4d}     Реактор: номинал             ║
║  Память: 7 слоёв     Рой: OK                                 ║
╚══════════════════════════════════════════════════════════════╝
""".strip()


def main() -> None:
    print(render())


if __name__ == "__main__":
    main()


__all__ = ["AuraView", "main", "render", "snapshot"]
