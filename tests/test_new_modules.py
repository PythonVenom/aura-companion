"""Тесты для модулей v8.2.0."""
from __future__ import annotations


def test_cores_detect():
    from aura.lore.cores import detect_core
    assert detect_core("sos помогите").id == "guardian"
    assert detect_core("мне плохо").id == "care"


def test_affinity_grows():
    from aura.core.affinity import Affinity, add_xp
    a = add_xp(50)
    assert a.xp >= 50


def test_quirks_wrap():
    from aura.lore.quirks import wrap
    result = wrap("Тест.")
    assert "Тест." in result


def test_receipts_chain():
    from aura.core.receipts import record, verify
    record("test_action", "test_actor", {"k": "v"})
    ok, count = verify()
    assert ok
    assert count >= 1


def test_rituals():
    from aura.core.rituals import morning_briefing, evening_ritual
    assert "Утро" in morning_briefing() or "утро" in morning_briefing()
    assert "Вечер" in evening_ritual() or "вечер" in evening_ritual()


def test_cluster_health():
    from aura.core.cluster_health import summary
    s = summary()
    assert s["total"] == 9


def test_i18n():
    from aura.lore.i18n import translate, set_lang
    for lang in ["ru", "en", "hi", "ta", "ko", "ja", "de"]:
        set_lang(lang)
        assert translate("greeting") != "greeting"
    set_lang("ru")


def test_backup_stats():
    from aura.core.backup import stats
    s = stats()
    assert "count" in s


def test_sandbox():
    from aura.core.sandbox import list_tenants, current_tenant
    assert current_tenant() is not None
    assert isinstance(list_tenants(), list)


def test_quiz():
    from aura.plugins.games.quiz import QuizSession
    s = QuizSession()
    q = s.start(3)
    assert q.text
    s.answer(q.answer)


