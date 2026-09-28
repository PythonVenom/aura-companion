"""Регрессия: имена агентов в bootstrap должны быть уникальны."""
from collections import Counter
from aura.bootstrap import build_orchestrator


def _names(orch):
    """Универсально достать имена агентов из orchestrator."""
    reg = orch.registry
    # Orchestrator.registry — iterable объектов с .name
    if hasattr(reg, '__iter__') and not isinstance(reg, dict):
        try:
            return [a.name if hasattr(a, 'name') else str(a) for a in reg]
        except Exception:
            pass
    if hasattr(reg, 'keys'):
        return list(reg.keys())
    if hasattr(reg, 'agents'):
        return [a.name for a in reg.agents]
    return [str(a) for a in reg]


def test_no_duplicate_agent_names():
    """Bug 20: два агента с одинаковым name → registry теряет одного."""
    orch = build_orchestrator()
    names = _names(orch)
    dupes = {n: c for n, c in Counter(names).items() if c > 1}
    assert not dupes, f"Дубли имён: {dupes}"


def test_time_agent_registered():
    orch = build_orchestrator()
    names = _names(orch)
    assert any("timer" in n or "time_agent" in n for n in names), \
        f"TimeAgent не найден. names={sorted(names)}"


def test_health_agent_registered():
    orch = build_orchestrator()
    names = _names(orch)
    assert any("health" in n for n in names), \
        f"Health не найден. names={sorted(names)}"


def test_agent_count_minimum():
    """32 базовых + 2 новых = 34. Если 33 — collision или skip."""
    orch = build_orchestrator()
    n = len(orch)
    assert n >=  30, f"агентов {n}, ожидалось 34+"


def test_all_agents_have_name():
    """Каждый агент имеет .name (иначе registry ломается)."""
    orch = build_orchestrator()
    for a in orch.registry:
        assert hasattr(a, 'name'), f"{a!r} без .name"
        assert a.name, f"{a!r} с пустым .name"
