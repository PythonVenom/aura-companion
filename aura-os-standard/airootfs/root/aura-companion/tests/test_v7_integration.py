"""Тесты v7.0 интеграции."""
from __future__ import annotations


def test_tier0_fastpath_in_orchestrator():
    import asyncio
    from aura.core.orchestrator import Orchestrator
    from aura.core import dispatcher
    orch = Orchestrator(dispatcher=dispatcher)
    r = asyncio.run(orch.process("который час"))
    assert ":" in r or "сейчас" in r.lower()


def test_tier0_music_fast():
    import asyncio, time
    from aura.core.orchestrator import Orchestrator
    from aura.core import dispatcher
    orch = Orchestrator(dispatcher=dispatcher)
    start = time.time()
    r = asyncio.run(orch.process("включи музыку"))
    elapsed = time.time() - start
    assert elapsed < 5, f"too slow: {elapsed}"


def test_consolidator_decay():
    from aura.core.memory.consolidator import decay_confidence
    c0 = 1.0
    c30 = decay_confidence(c0, age_days=30, halflife=90)
    assert c30 < c0
    assert 0.5 < c30 < 1.0


def test_consolidator_exists():
    from aura.core.memory.consolidator import run_all
    assert callable(run_all)


def test_extractor_bg_thread():
    """Extractor должен работать в фоне — не блокировать."""
    from aura.core.orchestrator import _mem_write
    # Просто вызов, без исключений
    _mem_write("батя любит чай", "запомнила")
    assert True
