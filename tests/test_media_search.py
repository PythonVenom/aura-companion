"""
Тесты для AgentMediaSearch.

Изоляция:
- Сканируются ТОЛЬКО временные папки (tmp_path), не реальные ~/Music
- subprocess.Popen и subprocess.run — mock, реальный VLC/mpv НЕ запускается
"""

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.media_search import AgentMediaSearch
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def music_dir(tmp_path):
    """Временная папка с фейковыми треками."""
    d = tmp_path / "music"
    d.mkdir()
    (d / "track_one.mp3").write_bytes(b"fake")
    (d / "track_two.flac").write_bytes(b"fake")
    (d / "song_three.wav").write_bytes(b"fake")
    (d / "readme.txt").write_text("not a track")
    return d


@pytest.fixture
def movie_dir(tmp_path):
    """Временная папка с фейковыми фильмами."""
    d = tmp_path / "movies"
    d.mkdir()
    (d / "movie_one.mp4").write_bytes(b"fake")
    (d / "movie_two.mkv").write_bytes(b"fake")
    return d


@pytest.fixture
def agent(music_dir, movie_dir) -> AgentMediaSearch:
    """Агент, привязанный только к временным папкам."""
    return AgentMediaSearch(
        music_dirs=[str(music_dir)],
        movie_dirs=[str(movie_dir)],
    )


class TestScan:
    def test_scans_music(self, agent: AgentMediaSearch) -> None:
        assert len(agent.media_cache["music"]) == 3

    def test_scans_movies(self, agent: AgentMediaSearch) -> None:
        assert len(agent.media_cache["movies"]) == 2

    def test_ignores_non_media(self, agent: AgentMediaSearch) -> None:
        titles = [m["title"] for m in agent.media_cache["music"]]
        assert "readme" not in titles


class TestCanHandle:
    @pytest.mark.parametrize("text", [
        "включи музыку города",
        "включи песню",
        "поставь трек",
        "включи фильм матрица",
        "список музыки",
        "какая музыка",
        "список фильмов",
        "пересканируй медиа",
        "останови музыку",
    ])
    def test_handles_media_commands(self, agent: AgentMediaSearch, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "громче",
        "погода",
    ])
    def test_ignores_other(self, agent: AgentMediaSearch, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestFind:
    def test_find_exact(self, agent: AgentMediaSearch) -> None:
        result = agent.find_media("track_one", kind="music")
        assert result is not None
        assert result["title"] == "track_one"

    def test_find_partial(self, agent: AgentMediaSearch) -> None:
        result = agent.find_media("two", kind="music")
        assert result is not None
        assert "two" in result["title"]

    def test_find_fuzzy(self, agent: AgentMediaSearch) -> None:
        result = agent.find_media("trak_one", kind="music")  # опечатка
        assert result is not None
        assert result["title"] == "track_one"

    def test_find_not_found(self, agent: AgentMediaSearch) -> None:
        result = agent.find_media("nonexistent_xyz", kind="music")
        assert result is None

    def test_find_in_movies(self, agent: AgentMediaSearch) -> None:
        result = agent.find_media("movie_one", kind="movie")
        assert result is not None
        assert result["title"] == "movie_one"


class TestPlayWithMock:
    @pytest.mark.asyncio
    @patch("aura.agents.media_search.subprocess.Popen")
    async def test_play_music_via_vlc(self, mock_popen, agent: AgentMediaSearch) -> None:
        mock_popen.return_value = MagicMock()

        response = await agent.handle(AgentRequest(text="включи музыку track_one"))

        assert response.status == AgentStatus.OK
        assert "Включаю" in response.text
        assert "track_one" in response.text
        # Проверяем, что вызван vlc
        args = mock_popen.call_args[0][0]
        assert args[0] == "vlc"
        assert "track_one.mp3" in args[-1]

    @pytest.mark.asyncio
    @patch("aura.agents.media_search.subprocess.Popen")
    async def test_play_not_found(self, mock_popen, agent: AgentMediaSearch) -> None:
        response = await agent.handle(AgentRequest(text="включи музыку nonexistent_xyz"))

        assert response.status == AgentStatus.OK
        assert "Не нашла" in response.text
        mock_popen.assert_not_called()


class TestList:
    @pytest.mark.asyncio
    async def test_list_music(self, agent: AgentMediaSearch) -> None:
        response = await agent.handle(AgentRequest(text="список музыки"))

        assert response.status == AgentStatus.OK
        assert "Треков" in response.text
        assert "track_one" in response.text

    @pytest.mark.asyncio
    async def test_list_movies(self, agent: AgentMediaSearch) -> None:
        response = await agent.handle(AgentRequest(text="список фильмов"))

        assert response.status == AgentStatus.OK
        assert "Фильмов" in response.text
        assert "movie_one" in response.text


class TestStop:
    @pytest.mark.asyncio
    @patch("aura.agents.media_search.subprocess.run")
    async def test_stop(self, mock_run, agent: AgentMediaSearch) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        response = await agent.handle(AgentRequest(text="останови музыку"))

        assert response.status == AgentStatus.OK
        assert "Остановила" in response.text


class TestRescan:
    @pytest.mark.asyncio
    async def test_rescan(self, agent: AgentMediaSearch) -> None:
        response = await agent.handle(AgentRequest(text="пересканируй медиа"))

        assert response.status == AgentStatus.OK
        assert "Пересканировала" in response.text


class TestUnknown:
    @pytest.mark.asyncio
    async def test_unknown(self, agent: AgentMediaSearch) -> None:
        response = await agent.handle(AgentRequest(text="привет"))
        assert response.status == AgentStatus.NOT_HANDLED
