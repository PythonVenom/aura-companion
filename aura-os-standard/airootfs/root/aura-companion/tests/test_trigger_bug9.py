"""Bug 9: триггер дублируется, потому что MAX меняет preview."""

from aura.agents.proactive import _normalize_preview, _extract_chat_cooldown_key


def test_normalize_strips_counter():
    assert _normalize_preview("1 | Прогуляться не хочешь") == "Прогуляться не хочешь"


def test_normalize_strips_time():
    assert _normalize_preview("Привет | 10:45") == "Привет"


def test_normalize_strips_both():
    assert _normalize_preview("1 | текст | 10:45") == "текст"


def test_normalize_idempotent():
    assert _normalize_preview("обычный текст") == "обычный текст"
