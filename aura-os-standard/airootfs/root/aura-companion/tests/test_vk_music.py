"""
Тесты для AgentVKMusic.

ВАЖНО:
- requests.get — mock, реальные VK запросы НЕ выполняются
- subprocess.Popen — mock, Firefox НЕ открывается
- Токен — фейковый, передаётся через DI (token_path)
"""

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.vk_music import AgentVKMusic
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def token_file(tmp_path):
    """Временный файл с фейковым токеном."""
    f = tmp_path / "vk_token.txt"
    f.write_text("fake_token_1234567890")
    return str(f)


@pytest.fixture
def agent(token_file) -> AgentVKMusic:
    return AgentVKMusic(token_path=token_file)


@pytest.fixture
def no_token_agent(tmp_path) -> AgentVKMusic:
    return AgentVKMusic(token_path=str(tmp_path / "nonexistent.txt"))


def make_vk_response(payload: dict) -> MagicMock:
    """Mock для requests.get — возвращает JSON с response."""
    mock = MagicMock()
    mock.json.return_value = payload
    return mock


class TestTokenLoading:
    def test_token_loaded(self, agent: AgentVKMusic) -> None:
        assert agent.token == "fake_token_1234567890"

    def test_token_not_found(self, no_token_agent: AgentVKMusic) -> None:
        assert no_token_agent.token is None


class TestCanHandle:
    @pytest.fixture(autouse=True)
    def _vk_active(self):
        """Bug 14 ph.2: VK ловит ambiguous только при last_active=vk."""
        from aura.agents import media_state
        media_state.set_active("vk")
        yield

    @pytest.mark.parametrize("text", [
        "включи музыку",
        "включи вк",
        "найди вк Radiohead",
        "найди музыку Radiohead",
        "добавь в плейлист",
        "лайкни",
        "поставь лайк",
        "открой вк",
    ])
    def test_handles_vk_commands(self, agent: AgentVKMusic, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "громче",
        "погода",
        "что такое Луна",  # это Internet, не VK
    ])
    def test_ignores_other(self, agent: AgentVKMusic, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestPlayWithMock:
    @pytest.mark.asyncio
    @patch("aura.agents.vk_music.subprocess.Popen")
    @patch("aura.agents.vk_music.requests.get")
    async def test_play_ok(self, mock_get, mock_popen, agent: AgentVKMusic) -> None:
        mock_get.return_value = make_vk_response({
            "response": {
                "items": [{
                    "id": 123,
                    "owner_id": -456,
                    "artist": "Radiohead",
                    "title": "Creep",
                }]
            }
        })
        mock_popen.return_value = MagicMock()

        response = await agent.handle(AgentRequest(text="включи музыку"))

        assert response.status == AgentStatus.OK
        assert "Radiohead" in response.text
        assert "Creep" in response.text
        mock_popen.assert_called_once()

    @pytest.mark.asyncio
    @patch("aura.agents.vk_music.requests.get")
    async def test_play_token_expired(self, mock_get, agent: AgentVKMusic) -> None:
        mock_get.return_value = make_vk_response({
            "error": {"error_code": 5, "error_msg": "User authorization failed"}
        })

        response = await agent.handle(AgentRequest(text="включи музыку"))

        assert response.status == AgentStatus.OK
        assert "истёк" in response.text or "Токен" in response.text

    @pytest.mark.asyncio
    async def test_play_no_token(self, no_token_agent: AgentVKMusic) -> None:
        response = await no_token_agent.handle(AgentRequest(text="включи музыку"))

        assert response.status == AgentStatus.OK
        assert "токен" in response.text.lower()


class TestSearchWithMock:
    @pytest.mark.asyncio
    @patch("aura.agents.vk_music.subprocess.Popen")
    @patch("aura.agents.vk_music.requests.get")
    async def test_search_ok(self, mock_get, mock_popen, agent: AgentVKMusic) -> None:
        mock_get.return_value = make_vk_response({
            "response": {
                "items": [{
                    "id": 789,
                    "owner_id": -111,
                    "artist": "Ai Mori",
                    "title": "My Way",
                }]
            }
        })
        mock_popen.return_value = MagicMock()

        response = await agent.handle(AgentRequest(text="найди вк Ai Mori"))

        assert response.status == AgentStatus.OK
        assert "Ai Mori" in response.text
        assert "My Way" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.vk_music.requests.get")
    async def test_search_not_found(self, mock_get, agent: AgentVKMusic) -> None:
        mock_get.return_value = make_vk_response({"response": {"items": []}})

        response = await agent.handle(AgentRequest(text="найди вк nonexistent"))

        assert response.status == AgentStatus.OK
        assert "Ничего не найдено" in response.text


class TestLikeWithMock:
    @pytest.mark.asyncio
    @patch("aura.agents.vk_music.requests.get")
    async def test_like_no_track(self, mock_get, agent: AgentVKMusic) -> None:
        """Без последнего трека — ошибка."""
        response = await agent.handle(AgentRequest(text="лайкни"))

        assert response.status == AgentStatus.OK
        assert "Нет трека" in response.text
        mock_get.assert_not_called()

    @pytest.mark.asyncio
    @patch("aura.agents.vk_music.subprocess.Popen")
    @patch("aura.agents.vk_music.requests.get")
    async def test_like_after_search(self, mock_get, mock_popen, agent: AgentVKMusic) -> None:
        """Сначала поиск, потом лайк — состояние сохраняется."""
        mock_popen.return_value = MagicMock()

        # Поиск — задаёт last_track
        mock_get.return_value = make_vk_response({
            "response": {
                "items": [{
                    "id": 123,
                    "owner_id": -456,
                    "artist": "A",
                    "title": "B",
                }]
            }
        })
        await agent.handle(AgentRequest(text="найди вк test"))

        # Лайк — использует last_track
        mock_get.return_value = make_vk_response({"response": 1})
        response = await agent.handle(AgentRequest(text="лайкни"))

        assert response.status == AgentStatus.OK
        assert "Лайк" in response.text or "❤️" in response.text


class TestOpenVKWithMock:
    @pytest.mark.asyncio
    @patch("aura.agents.vk_music.subprocess.Popen")
    async def test_open_vk(self, mock_popen, agent: AgentVKMusic) -> None:
        mock_popen.return_value = MagicMock()

        response = await agent.handle(AgentRequest(text="открой вк"))

        assert response.status == AgentStatus.OK
        assert "VK" in response.text
        args = mock_popen.call_args[0][0]
        assert args == ["firefox", "--new-tab", "https://vk.com/audios"]


class TestUnknown:
    @pytest.mark.asyncio
    async def test_unknown(self, agent: AgentVKMusic) -> None:
        response = await agent.handle(AgentRequest(text="привет"))
        assert response.status == AgentStatus.NOT_HANDLED


# --- регрессия: vk_music не перехватывает «вкладки» (Фаза 8.2) ---

def test_can_handle_vk_play(agent):
    """Bug 14 ph.2: «включи музыку» — наша, если last_active=vk."""
    from aura.agents import media_state
    media_state.set_active("vk")
    assert agent.can_handle(AgentRequest(text="включи музыку"))


def test_can_handle_vk_search(agent):
    """«найди трек» — наша."""
    assert agent.can_handle(AgentRequest(text="найди трек кино"))


def test_cannot_handle_find_tab(agent):
    """«найди вкладку макс» — НЕ наша, это browser_tabs.
    Раньше перехватывалось через SEARCH_KEYWORDS = «найди»."""
    assert not agent.can_handle(AgentRequest(text="найди вкладку макс"))


def test_cannot_handle_tab_word(agent):
    """Любая фраза со словом «вкладка» — не наша."""
    assert not agent.can_handle(AgentRequest(text="закрой вкладку"))
    assert not agent.can_handle(AgentRequest(text="какие вкладки открыты"))
    assert not agent.can_handle(AgentRequest(text="открой вкладку телеграм"))


def test_cannot_handle_tab_declension(agent):
    """Все падежи слова «вкладка»."""
    assert not agent.can_handle(AgentRequest(text="найди вкладку"))
    assert not agent.can_handle(AgentRequest(text="найди вкладки"))
    assert not agent.can_handle(AgentRequest(text="нет вкладок"))
