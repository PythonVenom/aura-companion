"""Bug 8: chat-имя в DM режется до одного слова.

«петруха чип тест финал» → chat="петруха", text="чип тест финал"
Должно: chat="петруха чип", text="тест финал".
"""

from unittest.mock import MagicMock

from aura.dialogue_manager import DialogueManager, Scenario


def _dm():
    sc = Scenario(
        name="messenger_send", agent="messenger",
        keywords=["напиши"], required_slots=["chat", "text"],
    )
    return DialogueManager(scenarios=[sc], get_agent=MagicMock(return_value=None)), sc


def test_two_word_chat_with_test_marker():
    dm, sc = _dm()
    dm.state.scenario = sc
    dm.state.started_at = 9e12
    dm._extract_slots("напиши петруха чип тест финал")
    assert dm.state.slots.get("chat") == "петруха чип"
    assert dm.state.slots.get("text") == "тест финал"


def test_single_word_chat():
    dm, sc = _dm()
    dm.state.scenario = sc
    dm.state.started_at = 9e12
    dm._extract_slots("напиши петруха привет")
    assert dm.state.slots.get("chat") == "петруха"
    assert dm.state.slots.get("text") == "привет"


def test_three_word_chat():
    dm, sc = _dm()
    dm.state.scenario = sc
    dm.state.started_at = 9e12
    dm._extract_slots("напиши иван петрович сидоров как дела")
    assert dm.state.slots.get("chat") == "иван петрович сидоров"
    assert dm.state.slots.get("text") == "как дела"
