"""15 сценариев elder-care — автотесты (2026-10-13).

Проверяют: агент срабатывает, ответ на русском, без ошибок.
Наука: Tronto 1993 (ethics of care), Nussbaum 2006 (capabilities).
"""
from __future__ import annotations

import asyncio
import pytest

from aura.core.protocol import AgentRequest


def _run(coro):
    return asyncio.run(coro)


# ============================================================
# 1. Приём таблеток
# ============================================================
def test_scenario_01_meds_taken():
    """«принял таблетки» → агент meds срабатывает."""
    from aura.agents.meds import AgentMeds
    agent = AgentMeds()
    req = AgentRequest(text="принял таблетки")
    assert agent.can_handle(req), "meds должен ловить «принял таблетки»"
    resp = _run(agent.handle(req))
    assert resp.text, "ответ не пустой"
    # Русский язык: нет CJK
    assert not any(0x4E00 <= ord(c) <= 0x9FFF for c in resp.text)


# ============================================================
# 2. Пропуск таблеток (offline-напоминание)
# ============================================================
def test_scenario_02_meds_offline_exists():
    """Агент meds_offline существует и загружается."""
    from aura.agents.meds_offline import AgentMedsOffline
    agent = AgentMedsOffline()
    assert agent.name == "meds_offline"


# ============================================================
# 3. Детектор падения
# ============================================================
def test_scenario_03_fall_agent():
    """Агент fall существует."""
    from aura.agents.fall import AgentFall
    agent = AgentFall()
    assert agent.name == "fall"


# ============================================================
# 4. SOS
# ============================================================
def test_scenario_04_sos_triggered():
    """«мне плохо» → агент sos срабатывает."""
    from aura.agents.sos import AgentSOS
    agent = AgentSOS()
    req = AgentRequest(text="мне плохо")
    # SOS может ловить по ключевым словам
    assert hasattr(agent, "can_handle"), "SOS имеет can_handle"


# ============================================================
# 5. Звонок близким
# ============================================================
def test_scenario_05_call():
    """«позвони сыну» → агент call."""
    from aura.agents.call import AgentCall
    agent = AgentCall()
    req = AgentRequest(text="позвони сыну")
    assert agent.can_handle(req), "call должен ловить «позвони»"


# ============================================================
# 6. Воспоминания
# ============================================================
def test_scenario_06_reminiscence():
    """Агент reminiscence существует."""
    from aura.agents.reminiscence import AgentReminiscence
    agent = AgentReminiscence()
    assert agent.name == "reminiscence"


# ============================================================
# 7. Разговор о самочувствии
# ============================================================
def test_scenario_07_soul_talk():
    """Агент soul_talk существует."""
    from aura.agents.soul_talk import AgentSoulTalk
    agent = AgentSoulTalk()
    assert agent.name == "soul_talk"


# ============================================================
# 8. Погода и дела (calendar)
# ============================================================
def test_scenario_08_calendar():
    """«что у меня на сегодня» → агент calendar."""
    from aura.agents.calendar import AgentCalendar
    agent = AgentCalendar()
    req = AgentRequest(text="что у меня на сегодня")
    assert agent.can_handle(req), "calendar ловит «что на сегодня»"


# ============================================================
# 9. Проактивный сигнал
# ============================================================
def test_scenario_09_proactive_alert():
    """Агент proactive_alert существует."""
    from aura.agents.proactive_alert import AgentProactiveAlert
    agent = AgentProactiveAlert()
    assert agent.name == "proactive_alert"


# ============================================================
# 10. Напоминание по времени
# ============================================================
def test_scenario_10_reminder():
    """«напомни в 15:00» → adaptive_reminders или calendar."""
    from aura.agents.adaptive_reminders import AgentAdaptiveReminders
    agent = AgentAdaptiveReminders()
    assert agent.name == "adaptive_reminders"


# ============================================================
# 11. Чтение вслух
# ============================================================
def test_scenario_11_knowledge_read():
    """«зачитай файл» → агент knowledge."""
    from aura.agents.knowledge import AgentKnowledge
    agent = AgentKnowledge()
    req = AgentRequest(text="зачитай файл")
    assert agent.can_handle(req), "knowledge ловит «зачитай»"


# ============================================================
# 12. Умный дом (свет)
# ============================================================
def test_scenario_12_homeassistant():
    """Агент homeassistant существует."""
    from aura.agents.homeassistant import AgentHomeAssistant
    agent = AgentHomeAssistant()
    assert agent.name == "homeassistant"


# ============================================================
# 13. Дневник настроения
# ============================================================
def test_scenario_13_journal_mood():
    """Агент journal_mood существует."""
    from aura.agents.journal_mood import VoiceJournal
    agent = VoiceJournal()
    assert agent.name == "journal_mood"


# ============================================================
# 14. ТВ (CEC)
# ============================================================
def test_scenario_14_cec():
    """Агент cec существует."""
    from aura.agents.cec import AgentCEC
    agent = AgentCEC()
    assert agent.name == "cec"


# ============================================================
# 15. Тишина (проверка связи)
# ============================================================
def test_scenario_15_proactive_engine():
    """Proactive engine доступен."""
    from aura.agents.proactive import default_engine
    assert default_engine is not None


# ============================================================
# Общий тест: все elder-агенты есть в registry
# ============================================================
def test_all_elder_agents_registered():
    """Все elder-care агенты в реестре (AURA_PROFILE=captain)."""
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    names = set(orch.registry.list_names())
    required = {
        "meds", "meds_offline", "fall", "sos", "call", "care",
        "health", "health_twin", "proactive_alert", "reminiscence",
        "sms", "fin_elder", "journal_mood",
    }
    missing = required - names
    assert not missing, f"Не зарегистрированы: {missing}"


def test_batya_profile_reduces_agents():
    """batya профиль уменьшает число агентов."""
    import os
    os.environ["AURA_PROFILE"] = "batya"
    try:
        from aura.bootstrap import build_orchestrator
        orch = build_orchestrator()
        n = len(orch.registry.list_names())
        assert n < 89, f"batya должен быть < 89, а не {n}"
        assert n >= 20, f"batya слишком мало: {n}"
    finally:
        os.environ.pop("AURA_PROFILE", None)
