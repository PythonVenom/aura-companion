"""Тесты для AgentBrowserTabs (протокол length-prefix)."""

from __future__ import annotations

import json
import struct
from unittest.mock import patch

import pytest

from aura.agents.browser_tabs import AgentBrowserTabs, KNOWN_URLS
from aura.core.protocol import AgentRequest, AgentStatus


# --- Фейковый сокет: собирает отправленное, отдаёт заготовленные ответы ---

class FakeSock:
    """Мок AF_UNIX сокета. Правильный диалог: [4 байта][JSON]."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []            # список распарсенных запросов
        self._buf = b""
        self._idx = 0
        self._raw_buf = b""

    def settimeout(self, t): pass
    def connect(self, path): pass

    def sendall(self, data):
        # data = [4 байта длины][JSON]
        length = struct.unpack("@I", data[:4])[0]
        payload = data[4:4 + length]
        self.sent.append(json.loads(payload.decode("utf-8")))

        reply = self.replies[self._idx] if self._idx < len(self.replies) else {}
        self._idx += 1
        reply_bytes = json.dumps(reply, ensure_ascii=False).encode("utf-8")
        self._buf = struct.pack("@I", len(reply_bytes)) + reply_bytes

    def recv(self, n):
        chunk = self._buf[:n]
        self._buf = self._buf[n:]
        return chunk

    def __enter__(self): return self
    def __exit__(self, *a): return False


def make_agent(replies):
    """Агент + FakeSock. Возвращает (agent, fake_sock)."""
    agent = AgentBrowserTabs()
    fake = FakeSock(replies)

    def fake_socket(*a, **kw):
        return fake

    patcher = patch("aura.agents.browser_tabs.socket.socket", side_effect=fake_socket)
    patcher.start()
    return agent, fake, patcher


# --- can_handle ---

def test_can_handle_list():
    a = AgentBrowserTabs()
    assert a.can_handle(AgentRequest(text="какие вкладки открыты"))


def test_can_handle_new():
    a = AgentBrowserTabs()
    assert a.can_handle(AgentRequest(text="новая вкладка"))


def test_can_handle_close():
    a = AgentBrowserTabs()
    assert a.can_handle(AgentRequest(text="закрой вкладку"))


def test_can_handle_find():
    a = AgentBrowserTabs()
    assert a.can_handle(AgentRequest(text="найди вкладку макс"))


def test_can_handle_open_vk():
    a = AgentBrowserTabs()
    assert a.can_handle(AgentRequest(text="открой вк"))


def test_can_handle_open_telegram():
    a = AgentBrowserTabs()
    assert a.can_handle(AgentRequest(text="открой телеграм"))


def test_cannot_handle_time():
    a = AgentBrowserTabs()
    assert not a.can_handle(AgentRequest(text="который час"))


def test_cannot_handle_random_open():
    """«открой холодильник» — не наша команда."""
    a = AgentBrowserTabs()
    assert not a.can_handle(AgentRequest(text="открой холодильник"))


# --- list_tabs ---

@pytest.mark.asyncio
async def test_list_tabs_ok():
    replies = [{"tabs": [
        {"id": 1, "title": "MAX", "active": True},
        {"id": 2, "title": "DeepSeek", "active": False},
    ]}]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="какие вкладки"))
    finally:
        p.stop()
    assert resp.status == AgentStatus.OK
    assert "MAX" in resp.text
    assert "DeepSeek" in resp.text
    assert fake.sent[0]["action"] == "list_tabs"


@pytest.mark.asyncio
async def test_list_tabs_empty():
    replies = [{"tabs": []}]
    agent, _, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="какие вкладки"))
    finally:
        p.stop()
    assert "нет" in resp.text.lower()


# --- new_tab ---

@pytest.mark.asyncio
async def test_new_tab_ok():
    replies = [{"success": True, "tabId": 5}]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="новая вкладка"))
    finally:
        p.stop()
    assert "Открыла" in resp.text
    assert fake.sent[0]["action"] == "open_tab"
    assert fake.sent[0]["url"] == "about:newtab"


@pytest.mark.asyncio
async def test_new_tab_bridge_not_running():
    agent = AgentBrowserTabs()

    def boom(*a, **kw):
        raise FileNotFoundError("no socket")

    with patch("aura.agents.browser_tabs.socket.socket", side_effect=boom):
        resp = await agent.handle(AgentRequest(text="новая вкладка"))
    assert "не запущен" in resp.text.lower()


# --- close ---

@pytest.mark.asyncio
async def test_close_active_tab_ok():
    """Без имени: сначала list_tabs, находим active, потом close_tab(id)."""
    replies = [
        {"tabs": [
            {"id": 1, "title": "A", "active": False},
            {"id": 7, "title": "B", "active": True},
        ]},
        {"success": True},
    ]
    agent, fake, p = make_agent(replies)
    try:
        # Bug 31: сначала подтверждение
        r1 = await agent.handle(AgentRequest(text="закрой вкладку"))
        assert "да" in r1.text.lower() or "нет" in r1.text.lower()
        resp = await agent.handle(AgentRequest(text="да"))
    finally:
        p.stop()
    assert "Закрыла" in resp.text
    assert fake.sent[0]["action"] == "list_tabs"
    assert fake.sent[1]["action"] == "close_tab"
    assert fake.sent[1]["tab_id"] == 7


@pytest.mark.asyncio
async def test_close_tab_by_name():
    replies = [{"success": True, "title": "MAX"}]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="закрой вкладку макс"))
    finally:
        p.stop()
    assert "Закрыла" in resp.text
    assert fake.sent[0]["action"] == "close_tab_by_name"
    assert fake.sent[0]["query"] == "макс"


@pytest.mark.asyncio
async def test_close_tab_by_name_not_found():
    replies = [{"error": "not found"}]
    agent, _, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="закрой вкладку крокодил"))
    finally:
        p.stop()
    assert "не найдена" in resp.text.lower()


# --- navigation ---

@pytest.mark.asyncio
async def test_next_tab():
    replies = [{"success": True}]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="следующая вкладка"))
    finally:
        p.stop()
    assert "следующ" in resp.text.lower()
    assert fake.sent[0]["action"] == "next_tab"


@pytest.mark.asyncio
async def test_prev_tab():
    replies = [{"success": True}]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="предыдущая вкладка"))
    finally:
        p.stop()
    assert "предыдущ" in resp.text.lower()
    assert fake.sent[0]["action"] == "prev_tab"


# --- find / activate ---

@pytest.mark.asyncio
async def test_find_and_activate_found():
    replies = [
        {"tabs": [{"id": 4, "title": "MAX"}]},
        {"success": True, "title": "MAX"},
    ]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="найди вкладку макс"))
    finally:
        p.stop()
    assert "Переключилась" in resp.text
    assert fake.sent[0]["action"] == "find_tab"
    assert fake.sent[0]["query"] == "макс"
    assert fake.sent[1]["action"] == "activate_tab"
    assert fake.sent[1]["tab_id"] == 4


@pytest.mark.asyncio
async def test_find_and_activate_not_found():
    replies = [{"tabs": []}]
    agent, _, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="найди вкладку крокодил"))
    finally:
        p.stop()
    assert "не найдена" in resp.text.lower()


# --- open_or_focus ---

@pytest.mark.asyncio
async def test_open_vk_focuses_if_open():
    """Боль из промта: «открой ВК» → если вкладка есть, переключиться."""
    replies = [
        {"tabs": [{"id": 3, "title": "ВКонтакте"}]},
        {"success": True, "title": "ВКонтакте"},
    ]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="открой вк"))
    finally:
        p.stop()
    assert "Переключилась" in resp.text
    assert fake.sent[0]["action"] == "find_tab"
    assert fake.sent[1]["action"] == "activate_tab"
    # НЕ должно быть open_tab — вкладка уже открыта
    assert all(s["action"] != "open_tab" for s in fake.sent)


@pytest.mark.asyncio
async def test_open_vk_opens_if_not_open():
    # 3 ответа: find_tab("вк") пусто, find_tab("vk") пусто, open_tab success
    replies = [
        {"tabs": []},
        {"tabs": []},
        {"success": True, "tabId": 9},
    ]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="открой вк"))
    finally:
        p.stop()
    assert "Открыла" in resp.text
    # 3 вызова: find_tab("вк"), find_tab("vk"), open_tab("https://vk.com")
    assert fake.sent[0]["action"] == "find_tab"
    assert fake.sent[0]["query"] == "вк"
    assert fake.sent[1]["action"] == "find_tab"
    assert fake.sent[1]["query"] == "vk"
    assert fake.sent[2]["action"] == "open_tab"
    assert fake.sent[2]["url"] == "https://vk.com"


@pytest.mark.asyncio
async def test_open_unknown_uses_search():
    """«открой что-то» — не в KNOWN_URLS, но starts with «открой»."""
    replies = [
        {"tabs": []},
        {"success": True, "tabId": 10},
    ]
    agent, fake, p = make_agent(replies)
    try:
        # «открой сайт X» — OPEN_KEYWORDS
        resp = await agent.handle(AgentRequest(text="открой сайт python"))
    finally:
        p.stop()
    assert fake.sent[-1]["action"] == "new_tab_search"


# --- _extract_after ---

def test_extract_after_basic():
    a = AgentBrowserTabs()
    assert a._extract_after("закрой вкладку макс", a.CLOSE_KEYWORDS) == "макс"


def test_extract_after_punctuation():
    a = AgentBrowserTabs()
    assert a._extract_after("найди вкладку макс!", a.FIND_KEYWORDS) == "макс"


def test_extract_after_empty():
    a = AgentBrowserTabs()
    assert a._extract_after("закрой вкладку", a.CLOSE_KEYWORDS) == ""


# --- KNOWN_URLS ---

def test_known_urls_vk():
    assert KNOWN_URLS["вк"] == "https://vk.com"


def test_known_urls_telegram():
    assert KNOWN_URLS["телеграм"] == "https://web.telegram.org"


def test_known_urls_youtube():
    assert KNOWN_URLS["youtube"] == "https://youtube.com"


# --- protocol: length-prefix ---

def test_send_command_uses_length_prefix():
    replies = [{"pong": True}]
    agent, fake, p = make_agent(replies)
    try:
        result = agent._send_command({"action": "ping"})
    finally:
        p.stop()
    assert result == {"pong": True}
    assert fake.sent[0] == {"action": "ping"}


def test_send_command_timeout():
    import socket as real_socket

    def timeout_socket(*a, **kw):
        raise real_socket.timeout("sim")

    agent = AgentBrowserTabs()
    with patch("aura.agents.browser_tabs.socket.socket", side_effect=timeout_socket):
        result = agent._send_command({"action": "ping"})
    assert result == {"error": "timeout"}


def test_send_command_file_not_found():
    agent = AgentBrowserTabs()

    def no_file(*a, **kw):
        raise FileNotFoundError("no socket")

    with patch("aura.agents.browser_tabs.socket.socket", side_effect=no_file):
        result = agent._send_command({"action": "ping"})
    assert result == {"error": "bridge_not_running"}


# --- Фаза 8.3: алиасы кириллица→латиница ---

def test_normalize_query_max():
    a = AgentBrowserTabs()
    assert a._normalize_query("макс") == "max"
    assert a._normalize_query("МАКС") == "max"


def test_normalize_query_vk():
    a = AgentBrowserTabs()
    assert a._normalize_query("вк") == "vk"
    assert a._normalize_query("вконтакте") == "vk"


def test_normalize_query_deepseek():
    a = AgentBrowserTabs()
    assert a._normalize_query("дипсик") == "deepseek"


def test_normalize_query_no_alias():
    a = AgentBrowserTabs()
    assert a._normalize_query("python") == "python"
    assert a._normalize_query("что-то") == "что-то"


@pytest.mark.asyncio
async def test_find_tab_via_normalization():
    """«найди вкладку макс»: сначала find_tab("макс") пусто,
    потом find_tab("max") находит — это и есть фикс Фазы 8.3."""
    replies = [
        {"tabs": []},                                    # find_tab("макс")
        {"tabs": [{"id": 7, "title": "MAX"}]},          # find_tab("max")
        {"success": True, "title": "MAX"},              # activate_tab
    ]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="найди вкладку макс"))
    finally:
        p.stop()
    assert "Переключилась" in resp.text
    assert "MAX" in resp.text
    # Проверяем последовательность запросов
    assert fake.sent[0]["action"] == "find_tab"
    assert fake.sent[0]["query"] == "макс"
    assert fake.sent[1]["action"] == "find_tab"
    assert fake.sent[1]["query"] == "max"
    assert fake.sent[2]["action"] == "activate_tab"
    assert fake.sent[2]["tab_id"] == 7


@pytest.mark.asyncio
async def test_find_tab_via_truncation():
    """T-one глотает окончания: «мак» вместо «макс».
    После нормализации "мак" — нет алиаса. Но "макс"[:3] = "мак",
    а "max"[:3] = "max" — должно найтись через truncation."""
    # Для «макс»: find_tab("макс") пусто, find_tab("max") пусто,
    # обрезка "мак" пусто, обрезка "max" находит.
    replies = [
        {"tabs": []},                                    # find_tab("макс")
        {"tabs": []},                                    # find_tab("max")
        {"tabs": []},                                    # find_tab("мак")
        {"tabs": [{"id": 7, "title": "MAX"}]},          # find_tab("max") — truncation
        {"success": True, "title": "MAX"},              # activate_tab
    ]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="найди вкладку макс"))
    finally:
        p.stop()
    assert "Переключилась" in resp.text


# --- Фаза 8.3.1: T-one обрезал «макс» → «мак» ---

def test_normalize_query_mak():
    """«мак» (обрезок T-one) → «max»."""
    a = AgentBrowserTabs()
    assert a._normalize_query("мак") == "max"


@pytest.mark.asyncio
async def test_find_tab_short_mak():
    """«найди вкладку мак» — T-one обрезал, но алиас спасает."""
    replies = [
        {"tabs": []},                                    # find_tab("мак")
        {"tabs": [{"id": 7, "title": "MAX"}]},          # find_tab("max")
        {"success": True, "title": "MAX"},              # activate_tab
    ]
    agent, fake, p = make_agent(replies)
    try:
        resp = await agent.handle(AgentRequest(text="найди вкладку мак"))
    finally:
        p.stop()
    assert "Переключилась" in resp.text
    assert fake.sent[0]["query"] == "мак"
    assert fake.sent[1]["query"] == "max"
