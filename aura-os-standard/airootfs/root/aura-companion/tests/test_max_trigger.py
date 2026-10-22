"""Bug 2+3+4: max_new_message — все чаты, пропуск «Вы:», порядок не важен."""

from __future__ import annotations

from aura.agents.proactive import max_new_message_trigger


class _Messenger:
    def __init__(self, previews):
        self._p = previews

    def get_all_previews(self):
        return list(self._p)


def _setup(previews):
    box = {"m": _Messenger(previews)}
    def get_agent(name):
        return box["m"] if name == "messenger" else None
    return get_agent, box


def test_first_run_populates_without_trigger():
    """Первый запуск — populate без триггера (иначе спам после рестарта)."""
    get_agent, _ = _setup([{"chat": "Аня", "preview": "привет"}])
    t = max_new_message_trigger(get_agent)
    state = {}
    assert t.condition(state) is False
    assert "Аня:привет" in state.get("max_seen_keys", [])


def test_all_chats_tracked():
    """Bug 2: отслеживаем все чаты, не только верхний."""
    get_agent, _ = _setup([
        {"chat": "Аня", "preview": "привет"},
        {"chat": "Борис", "preview": "как дела"},
    ])
    t = max_new_message_trigger(get_agent)
    state = {}
    t.condition(state)
    keys = state.get("max_seen_keys", [])
    assert "Аня:привет" in keys
    assert "Борис:как дела" in keys


def test_new_message_in_non_first_chat():
    """Bug 2: новое сообщение в чате, который НЕ первый в списке."""
    get_agent, box = _setup([
        {"chat": "Аня", "preview": "привет"},
        {"chat": "Борис", "preview": "как дела"},
    ])
    t = max_new_message_trigger(get_agent)
    state = {}
    t.condition(state)

    box["m"] = _Messenger([
        {"chat": "Аня", "preview": "привет"},
        {"chat": "Борис", "preview": "новое сообщение"},
    ])
    assert t.condition(state) is True


def test_own_messages_skipped():
    """Bug 3: «Вы: ...» — не триггерить."""
    get_agent, _ = _setup([
        {"chat": "Аня", "preview": "Вы: привет"},
        {"chat": "Борис", "preview": "Вы: ок"},
    ])
    t = max_new_message_trigger(get_agent)
    state = {}
    assert t.condition(state) is False


def test_reorder_no_trigger():
    """Bug 4: перестановка чатов — не триггер."""
    get_agent, box = _setup([
        {"chat": "Аня", "preview": "привет"},
        {"chat": "Борис", "preview": "как дела"},
    ])
    t = max_new_message_trigger(get_agent)
    state = {}
    t.condition(state)

    box["m"] = _Messenger([
        {"chat": "Борис", "preview": "как дела"},
        {"chat": "Аня", "preview": "привет"},
    ])
    assert t.condition(state) is False


def test_delete_chat_no_trigger():
    """Удаление чата — не триггер."""
    get_agent, box = _setup([
        {"chat": "Аня", "preview": "привет"},
        {"chat": "Борис", "preview": "как дела"},
    ])
    t = max_new_message_trigger(get_agent)
    state = {}
    t.condition(state)

    box["m"] = _Messenger([
        {"chat": "Борис", "preview": "как дела"},
    ])
    assert t.condition(state) is False


def test_garbage_empty_previews_no_trigger():
    get_agent, _ = _setup([])
    t = max_new_message_trigger(get_agent)
    state = {}
    assert t.condition(state) is False
