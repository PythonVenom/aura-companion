"""
Тесты для AgentScreenReader.

ВАЖНО: Все тесты используют mock для subprocess.
Реальные maim/tesseract/xdotool НЕ вызываются.
"""

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.screen_reader import AgentScreenReader
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent() -> AgentScreenReader:
    return AgentScreenReader()


class TestCanHandle:
    @pytest.mark.parametrize("text", [
        "прочитай экран",
        "что на экране",
        "прочитай окно",
        "что в окне",
        "активное окно",
        "какое окно",
    ])
    def test_handles_screen_commands(self, agent: AgentScreenReader, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "громче",
        "погода",
    ])
    def test_ignores_other(self, agent: AgentScreenReader, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestActiveWindow:
    @pytest.mark.asyncio
    @patch("aura.agents.screen_reader.subprocess.run")
    async def test_active_window_ok(self, mock_run, agent: AgentScreenReader) -> None:
        mock_run.return_value = MagicMock(stdout="Firefox\n", returncode=0)

        response = await agent.handle(AgentRequest(text="активное окно"))

        assert response.status == AgentStatus.OK
        assert "Firefox" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.screen_reader.subprocess.run")
    async def test_active_window_empty(self, mock_run, agent: AgentScreenReader) -> None:
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        response = await agent.handle(AgentRequest(text="активное окно"))

        assert response.status == AgentStatus.OK
        assert "Не удалось" in response.text


class TestReadScreen:
    @pytest.mark.asyncio
    @patch("aura.agents.screen_reader.os.remove")
    @patch("aura.agents.screen_reader.os.close")
    @patch("aura.agents.screen_reader.tempfile.mkstemp")
    @patch("aura.agents.screen_reader.subprocess.run")
    async def test_read_screen_ok(
        self, mock_run, mock_mkstemp, mock_close, mock_remove, agent: AgentScreenReader
    ) -> None:
        mock_mkstemp.return_value = (99, "/tmp/aura_test.png")

        # 1-й вызов: maim (скриншот)
        # 2-й вызов: tesseract (OCR)
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0, stdout="Привет мир\n"),
        ]

        response = await agent.handle(AgentRequest(text="прочитай экран"))

        assert response.status == AgentStatus.OK
        assert "Привет" in response.text
        assert mock_run.call_count == 2

    @pytest.mark.asyncio
    @patch("aura.agents.screen_reader.os.remove")
    @patch("aura.agents.screen_reader.os.close")
    @patch("aura.agents.screen_reader.tempfile.mkstemp")
    @patch("aura.agents.screen_reader.subprocess.run")
    async def test_read_screen_empty(
        self, mock_run, mock_mkstemp, mock_close, mock_remove, agent: AgentScreenReader
    ) -> None:
        mock_mkstemp.return_value = (99, "/tmp/aura_test.png")
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0, stdout=""),
        ]

        response = await agent.handle(AgentRequest(text="прочитай экран"))

        assert response.status == AgentStatus.OK
        assert "нет распознаваемого" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.screen_reader.os.remove")
    @patch("aura.agents.screen_reader.os.close")
    @patch("aura.agents.screen_reader.tempfile.mkstemp")
    @patch("aura.agents.screen_reader.subprocess.run")
    async def test_read_screen_maim_fails(
        self, mock_run, mock_mkstemp, mock_close, mock_remove, agent: AgentScreenReader
    ) -> None:
        mock_mkstemp.return_value = (99, "/tmp/aura_test.png")
        mock_run.return_value = MagicMock(returncode=1, stderr="maim not found")

        response = await agent.handle(AgentRequest(text="прочитай экран"))

        assert response.status == AgentStatus.OK
        assert "Не удалось сделать скриншот" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.screen_reader.os.remove")
    @patch("aura.agents.screen_reader.os.close")
    @patch("aura.agents.screen_reader.tempfile.mkstemp")
    @patch("aura.agents.screen_reader.subprocess.run")
    async def test_read_screen_truncates(
        self, mock_run, mock_mkstemp, mock_close, mock_remove, agent: AgentScreenReader
    ) -> None:
        mock_mkstemp.return_value = (99, "/tmp/aura_test.png")
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0, stdout="x" * 2000),
        ]

        response = await agent.handle(AgentRequest(text="прочитай экран"))

        assert response.status == AgentStatus.OK
        assert response.text.endswith("...")
        assert len(response.text) < 900


class TestReadWindow:
    @pytest.mark.asyncio
    @patch("aura.agents.screen_reader.os.remove")
    @patch("aura.agents.screen_reader.os.close")
    @patch("aura.agents.screen_reader.tempfile.mkstemp")
    @patch("aura.agents.screen_reader.subprocess.run")
    async def test_read_window_ok(
        self, mock_run, mock_mkstemp, mock_close, mock_remove, agent: AgentScreenReader
    ) -> None:
        mock_mkstemp.return_value = (99, "/tmp/aura_test.png")
        # 1: xdotool (получить id), 2: maim (скриншот окна), 3: tesseract
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="12345\n"),
            MagicMock(returncode=0),
            MagicMock(returncode=0, stdout="Текст окна"),
        ]

        response = await agent.handle(AgentRequest(text="прочитай окно"))

        assert response.status == AgentStatus.OK
        assert "Текст окна" in response.text


class TestUnknown:
    @pytest.mark.asyncio
    async def test_unknown_returns_not_handled(self, agent: AgentScreenReader) -> None:
        response = await agent.handle(AgentRequest(text="привет"))
        assert response.status == AgentStatus.NOT_HANDLED
