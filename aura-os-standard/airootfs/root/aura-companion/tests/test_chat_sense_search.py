"""ChatSense: search_chats."""
from aura.agents.chat_sense import search_chats


def test_search_by_name():
    items = [
        {"name": "Аня", "preview": "привет"},
        {"name": "Борис", "preview": "как дела"},
    ]
    r = search_chats(items, "Аня")
    assert len(r) == 1


def test_search_by_preview():
    items = [
        {"name": "Аня", "preview": "купить хлеб"},
        {"name": "Борис", "preview": "привет"},
    ]
    r = search_chats(items, "хлеб")
    assert len(r) == 1


def test_search_case_insensitive():
    items = [{"name": "Anya", "preview": "Hello World"}]
    assert len(search_chats(items, "HELLO")) == 1


def test_search_empty_query():
    assert search_chats([], "") == []


def test_search_no_match():
    items = [{"name": "Аня", "preview": "привет"}]
    assert search_chats(items, "xxx") == []
