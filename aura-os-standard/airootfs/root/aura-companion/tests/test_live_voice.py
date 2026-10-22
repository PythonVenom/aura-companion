"""Regression: live-тест голосом — Bug E (числа-слова) + Bug F (тс→Тест)."""
import asyncio
import pytest
from aura.agents.time_agent import AgentTimeAgent
from aura.agents.massage import AgentMassage
from aura.core.protocol import AgentRequest


CASES = [
    ("time",    "таймер тридцать секунд", "30"),
    ("time",    "таймер 30 секунд",       "30"),
    ("massage", "сессия Тест 30",         "Тест"),
    ("massage", "сессия тс 30",           "Тест"),
]


@pytest.mark.parametrize("kind,text,needle", CASES)
def test_live_voice_regression(kind, text, needle):
    agent = AgentTimeAgent() if kind == "time" else AgentMassage()
    r = asyncio.run(agent.handle(AgentRequest(text=text)))
    assert needle.lower() in (r.text or "").lower(), f"{text!r} -> {r.text!r}"
