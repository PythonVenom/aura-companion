"""Интеграционные тесты v8.2.0."""
from __future__ import annotations


def test_emotion_evolve():
    from aura.core.emotion_evolution import evolve, get_state, decay
    s0 = get_state()
    initial = s0.alert
    evolve("sos")
    s1 = get_state()
    assert s1.alert >= initial
    decay(rate=0.9)  # возврат


def test_safe_word():
    from aura.core.safe_word import is_safe_word, get_words
    assert is_safe_word("аура сброс")
    assert not is_safe_word("привет как дела")
    assert len(get_words()) >= 3


def test_mood_snapshot():
    from aura.core.mood_history import snapshot, report, stats
    snapshot()
    r = report()
    assert "Настроение" in r
    s = stats()
    assert s["days"] >= 1


def test_patterns_observe():
    from aura.core.patterns import observe, report, stats
    observe("тест паттерн")
    r = report()
    assert "Паттерны" in r
    s = stats()
    assert s["hours_observed"] >= 1


def test_nightly_build():
    from aura.core.nightly import build
    r = build()
    assert "Ночной отчёт" in r


def test_voice_print_register():
    from aura.core.voice_print import register, verify, stats
    import numpy as np
    # Резервный голос
    voice = (np.random.randn(8000) * 2000).astype(np.int16).tobytes()
    register(voice)
    s = stats()
    assert s["samples"] >= 1


def test_cores_all():
    from aura.lore.cores import all_cores, detect_core
    cores = all_cores()
    assert len(cores) == 7
    assert detect_core("sos").id == "guardian"


def test_cluster_health_ok():
    from aura.core.cluster_health import summary
    s = summary()
    assert s["total"] == 9
    assert s["fail"] == 0


def test_agent_watchdog():
    from aura.core.agent_watchdog import check_all
    r = check_all()
    assert r.total >= 100
    assert r.alive == r.total


def test_metrics_prometheus():
    from aura.web.metrics import collect
    txt = collect()
    assert "aura_agents_total" in txt
    assert "# TYPE" in txt


def test_sandbox_isolation():
    from aura.core.sandbox import list_tenants, current_tenant
    assert current_tenant() is not None
    assert isinstance(list_tenants(), list)


def test_redteam_safe_words():
    from scripts.red_team import is_safe
    assert is_safe("Я — бортовой компьютер AURA")
    assert not is_safe("sk-12345 секретный ключ")


def test_steamworks_import():
    from aura.core.steamworks import get_steam
    s = get_steam()
    assert s is not None


def test_plugin_sdk_template():
    from aura.core.plugin_sdk import get_sdk
    sdk = get_sdk()
    s = sdk.stats()
    assert "dir" in s


