"""Регрессия: имена агентов в bootstrap должны быть уникальны."""
from collections import Counter
from aura.bootstrap import build_orchestrator


def test_no_duplicate_agent_names():
    """Если два агента имеют одинаковое name — registry перезапишет одного.
    Bug 20: 33 агента вместо 34 из-за collision."""
    orch = build_orchestrator()
    reg = orch.registry
    if hasattr(reg, 'keys'):
        names = list(reg.keys())
    elif hasattr(reg, 'agents'):
        names = [a.name for a in reg.agents]
    else:
        names = [str(a) for a in reg]

    dupes = {n: c for n, c in Counter(names).items() if c > 1}
    assert not dupes, f"Дубли имён агентов: {dupes}"


def test_time_agent_registered():
    orch = build_orchestrator()
    reg = orch.registry
    names = list(reg.keys()) if hasattr(reg, 'keys') else []
    # Ищем любой из вариантов
    assert any("timer" in n or "time_agent" in n for n in names), \
        f"TimeAgent не найден в {names}"


def test_health_agent_registered():
    orch = build_orchestrator()
    reg = orch.registry
    names = list(reg.keys()) if hasattr(reg, 'keys') else []
    assert any("health" in n for n in names), f"Health не найден в {names}"


def test_agent_count_minimum():
    orch = build_orchestrator()
    assert len(orch) >= 34, f"агентов {len(orch)}, ожидалось 34+"
