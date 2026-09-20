"""
Тесты для AgentBrowserTabs.

ВАЖНО: Все тесты используют mock для socket.socket.
Реальный Firefox bridge НЕ вызывается.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.browser_tabs import AgentBrowserTabs
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent() -> AgentBrowserTabs:
    return AgentBrowserTabs(socket_path="/tmp/test_aura.sock")


def make_socket_mock(response: dict | None) -> MagicMock:
    """Mock для socket, который возвращает response."""
    mock_sock = MagicMock()
    if response is not None:
        mock_sock.recv.return_value = (json.dumps(response) + "\n").encode("utf-8")
    else:
        mock_sock.recv.return_value = b""
    mock_sock.__enter__ = lambda self: self
    mock_sock.__exit__ = lambda self, *a: None
    return mock_sock


class TestCanHandle:
    @pytest.mark.parametrize("text", [
        "новая вкладка",
        "открой вкладку",
        "закрой вкладку",
        "следующая вкладка",
        "предыдущая вкладка",
        "список вкладок",
    ])
    def test_handles_browser_commands(self, agent: AgentBrowserTabs, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "громче",
        "погода",
    ])
    def test_ignores_other(self, agent: AgentBrowserTabs, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestNewTab:
    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_new_tab_ok(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        mock_socket_cls.return_value = make_socket_mock({"ok": True})

        response = await agent.handle(AgentRequest(text="новая вкладка"))

        assert response.status == AgentStatus.OK
        assert "новую вкладку" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_new_tab_bridge_not_running(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        mock_socket_cls.return_value = make_socket_mock({"error": "bridge_not_running"})

        response = await agent.handle(AgentRequest(text="новая вкладка"))

        assert response.status == AgentStatus.OK
        assert "bridge не запущен" in response.text


class TestCloseTab:
    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_close_tab_ok(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        mock_socket_cls.return_value = make_socket_mock({"ok": True})

        response = await agent.handle(AgentRequest(text="закрой вкладку"))

        assert response.status == AgentStatus.OK
        assert "Закрыла" in response.text


class TestNavigation:
    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_next_tab(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        mock_socket_cls.return_value = make_socket_mock({"ok": True})

        response = await agent.handle(AgentRequest(text="следующая вкладка"))

        assert response.status == AgentStatus.OK
        assert "следующую" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_prev_tab(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        mock_socket_cls.return_value = make_socket_mock({"ok": True})

        response = await agent.handle(AgentRequest(text="предыдущая вкладка"))

        assert response.status == AgentStatus.OK
        assert "предыдущую" in response.text


class TestListTabs:
    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_list_tabs_ok(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        mock_socket_cls.return_value = make_socket_mock({
            "tabs": [
                {"title": "GitHub"},
                {"title": "YouTube"},
                {"title": "Wikipedia"},
            ]
        })

        response = await agent.handle(AgentRequest(text="список вкладок"))

        assert response.status == AgentStatus.OK
        assert "GitHub" in response.text
        assert "YouTube" in response.text
        assert "3" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_list_tabs_empty(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        mock_socket_cls.return_value = make_socket_mock({"tabs": []})

        response = await agent.handle(AgentRequest(text="список вкладок"))

        assert response.status == AgentStatus.OK
        assert "нет" in response.text.lower()


class TestErrors:
    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_file_not_found(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = FileNotFoundError("no socket")
        mock_sock.__enter__ = lambda self: self
        mock_sock.__exit__ = lambda self, *a: None
        mock_socket_cls.return_value = mock_sock

        response = await agent.handle(AgentRequest(text="новая вкладка"))

        assert response.status == AgentStatus.OK
        assert "bridge не запущен" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.browser_tabs.socket.socket")
    async def test_timeout(self, mock_socket_cls, agent: AgentBrowserTabs) -> None:
        import socket as sock_mod

        mock_sock = MagicMock()
        mock_sock.connect.side_effect = sock_mod.timeout("timeout")
        mock_sock.__enter__ = lambda self: self
        mock_sock.__exit__ = lambda self, *a: None
        mock_socket_cls.return_value = mock_sock

        response = await agent.handle(AgentRequest(text="список вкладок"))

        assert response.status == AgentStatus.OK
        assert "не ответил" in response.text


class TestUnknown:
    @pytest.mark.asyncio
    async def test_unknown_returns_not_handled(self, agent: AgentBrowserTabs) -> None:
        response = await agent.handle(AgentRequest(text="привет"))
        assert response.status == AgentStatus.NOT_HANDLED
