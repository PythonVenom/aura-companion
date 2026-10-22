"""ChatSense: suggest_reply, is_spam, search_chats."""
from aura.agents.chat_sense import suggest_reply, is_spam, search_chats


def test_reply_greeting():
    assert "ривет" in suggest_reply("привет")


def test_reply_question():
    assert len(suggest_reply("как дела?")) > 5


def test_reply_empty():
    assert suggest_reply("") == ""


def test_spam_skidka():
    assert is_spam("Магазин", "СКИДКА 50%") is True


def test_spam_casino():
    assert is_spam("Casino", "казино играй") is True


def test_spam_normal():
    assert is_spam("Аня", "привет, как дела?") is False


def test_spam_empty():
    assert is_spam("Аня", "") is True


def test_search_by_name():
    items = [{"name": "Аня", "preview": "привет"}, {"name": "Боря", "preview": "x"}]
    assert len(search_chats(items, "аня")) == 1


def test_search_by_preview():
    items = [{"name": "Аня", "preview": "купить хлеб"}]
    assert len(search_chats(items, "хлеб")) == 1


def test_search_case_insensitive():
    items = [{"name": "Anya", "preview": "Hello World"}]
    assert len(search_chats(items, "HELLO")) == 1


def test_search_empty_query():
    assert search_chats([], "") == []


def test_search_no_match():
    assert search_chats([{"name": "Аня", "preview": "привет"}], "xxx") == []
