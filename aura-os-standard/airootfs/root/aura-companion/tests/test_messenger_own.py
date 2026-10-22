"""Bug 13: не триггерить на собственные отправленные сообщения."""

import time
from aura.agents import messenger as m


def test_remember_and_check():
    m._sent_recent.clear()
    m._remember_sent("Аня", "привет")
    assert m.is_own_message("Аня", "привет") is True


def test_other_chat_not_match():
    m._sent_recent.clear()
    m._remember_sent("Аня", "привет")
    assert m.is_own_message("Борис", "привет") is False


def test_substring_match():
    """MAX может добавить '1 | ' или timestamp."""
    m._sent_recent.clear()
    m._remember_sent("Аня", "привет")
    assert m.is_own_message("Аня", "1 | привет | 11:20") is True


def test_ttl_expires():
    m._sent_recent.clear()
    m._sent_recent.append(("Аня", "старое", time.time() - 400))
    assert m.is_own_message("Аня", "старое") is False


def test_empty_text_no_match():
    m._sent_recent.clear()
    assert m.is_own_message("Аня", "") is False
