"""
Агент VK Music.

Управляет музыкой ВКонтакте: поиск, воспроизведение, лайки, плейлисты.
Токен — в vk_token.txt (4 пути поиска).

По науке:
- Изолирован (requests + subprocess)
- Тестируем (mock для requests и subprocess)
- Не знает про AuraCore
- Состояние: last_track, last_track_id — как в монолите
"""

from __future__ import annotations

import os
import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


class AgentVKMusic(BaseAgent):
    """
    Агент VK Music.

    Обрабатывает:
    - "включи музыку" / "включи вк" → рекомендации
    - "найди <исполнитель>" → поиск трека
    - "добавь в плейлист" → add_to_playlist
    - "лайкни" / "нравится" → like_track
    - "открой вк" → открыть vk.com/audios в Firefox
    """

    name = "vk_music"

    PLAY_KEYWORDS = ("включи музыку", "включи вк", "включи вконтакте",
                     "включи песню вк", "вк музыка")
    SEARCH_KEYWORDS = ("найди", "поиск")
    ADD_KEYWORDS = ("добавь в плейлист", "добавь песню", "добавь трек")
    LIKE_KEYWORDS = ("лайкни", "нравится", "поставь лайк")
    OPEN_KEYWORDS = ("открой вк", "открой музыку")

    TOKEN_PATHS = [
        "vk_token.txt",
        os.path.expanduser("~/aura_project/vk_token.txt"),
        os.path.expanduser("~/vk_token.txt"),
        "./vk_token.txt",
    ]

    def __init__(self, token_path: str | None = None) -> None:
        super().__init__()
        self.token: str | None = None
        self.last_track: dict | None = None
        self.last_track_id: str | None = None
        self._load_token(token_path)

    def _load_token(self, token_path: str | None = None) -> bool:
        """Загрузить VK токен. Если token_path задан — только его."""
        paths = [token_path] if token_path else self.TOKEN_PATHS
        for path in paths:
            if path and os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        token = f.read().strip()
                    if token and len(token) > 10:
                        self.token = token
                        return True
                except Exception:
                    pass
        return False

    def _vk_request(self, method: str, params: dict) -> dict:
        if not REQUESTS_OK:
            return {"error": "requests не установлен"}
        if not self.token:
            return {"error": "Токен не найден"}

        try:
            params["access_token"] = self.token
            params["v"] = "5.131"
            url = f"https://api.vk.com/method/{method}"
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        # Защита: «вкладка/вкладки/вкладок» — не наша тема,
        # это browser_tabs. Не перехватываем, даже если есть «найди».
        if "вкладк" in text or "вкладок" in text:
            return False
        # Защита: «чат» — это messenger, не мы.
        if "чат" in text:
            return False
        keywords = (
            self.PLAY_KEYWORDS
            + self.SEARCH_KEYWORDS
            + self.ADD_KEYWORDS
            + self.LIKE_KEYWORDS
            + self.OPEN_KEYWORDS
        )
        return any(kw in text for kw in keywords)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        # Порядок важен: точные фразы — раньше
        if any(kw in text for kw in self.OPEN_KEYWORDS):
            return AgentResponse.ok(self.open_vk(), self.name)

        if any(kw in text for kw in self.ADD_KEYWORDS):
            return AgentResponse.ok(self.add_to_playlist(), self.name)

        if any(kw in text for kw in self.LIKE_KEYWORDS):
            return AgentResponse.ok(self.like_track(), self.name)

        if any(kw in text for kw in self.PLAY_KEYWORDS):
            return AgentResponse.ok(self.play(), self.name)

        # "найди" — только если есть "вк" или "музык" (иначе перехватит AgentInternet)
        if ("вк" in text or "музык" in text or "песн" in text) and any(
            kw in text for kw in self.SEARCH_KEYWORDS
        ):
            query = self._extract_query(text)
            return AgentResponse.ok(self.search_track(query), self.name)

        return AgentResponse.not_handled(self.name)

    # --- Действия ---

    def play(self) -> str:
        if not self.token:
            return "❌ VK токен не найден"

        try:
            result = self._vk_request("audio.getRecommendations", {"count": 5})

            if "error" in result:
                err = result["error"]
                if isinstance(err, dict) and err.get("error_code") == 5:
                    return "❌ Токен истёк. Получите новый на vkhost.github.io"
                return f"❌ Ошибка VK: {err}"

            items = result.get("response", {}).get("items", [])
            if not items:
                return "❌ Нет рекомендаций. Попробуйте 'найди [исполнитель]'"

            track = items[0]
            self.last_track = track
            self.last_track_id = track.get("id")

            artist = track.get("artist", "Неизвестный")
            title = track.get("title", "Без названия")

            track_url = f"https://vk.com/audio{track.get('owner_id')}_{track.get('id')}"
            subprocess.Popen(
                ["firefox", "--new-tab", track_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return f"🎵 Включаю: {artist} - {title}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def search_track(self, query: str) -> str:
        if not self.token:
            return "❌ Токен не найден"
        if not query:
            return "❌ Что искать?"

        try:
            result = self._vk_request("audio.search", {
                "q": query,
                "count": 5,
                "sort": 2,
            })

            if "error" in result:
                return f"❌ Ошибка VK: {result['error']}"

            items = result.get("response", {}).get("items", [])
            if not items:
                return f"❌ Ничего не найдено по '{query}'"

            track = items[0]
            self.last_track = track
            self.last_track_id = track.get("id")

            artist = track.get("artist", "Неизвестный")
            title = track.get("title", "Без названия")

            track_url = f"https://vk.com/audio{track.get('owner_id')}_{track.get('id')}"
            subprocess.Popen(
                ["firefox", "--new-tab", track_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            return f"🎵 Нашла: {artist} - {title}"
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"

    def add_to_playlist(self) -> str:
        if not self.token:
            return "❌ Токен не найден"
        if not self.last_track:
            return "❌ Нет трека. Сначала 'включи музыку' или 'найди [запрос]'"

        try:
            track_id = self.last_track.get("id")
            owner_id = self.last_track.get("owner_id")

            if not track_id or not owner_id:
                return "❌ Неверные данные трека"

            result = self._vk_request("audio.add", {
                "audio_id": track_id,
                "owner_id": owner_id,
            })

            if "error" in result:
                return f"❌ Ошибка VK: {result['error']}"

            if "response" in result:
                return f"✅ Добавлено в плейлист: {self.last_track.get('title')}"
            return "❌ Не удалось добавить"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def like_track(self) -> str:
        if not self.token:
            return "❌ Токен не найден"
        if not self.last_track:
            return "❌ Нет трека. Сначала 'включи музыку' или 'найди [запрос]'"

        try:
            track_id = self.last_track.get("id")
            owner_id = self.last_track.get("owner_id")

            if not track_id or not owner_id:
                return "❌ Неверные данные трека"

            result = self._vk_request("audio.setLike", {
                "audio_id": track_id,
                "owner_id": owner_id,
                "like": 1,
            })

            if "error" in result:
                return f"❌ Ошибка VK: {result['error']}"

            if "response" in result:
                return f"❤️ Лайк: {self.last_track.get('title')}"
            return "❌ Не удалось поставить лайк"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def open_vk(self) -> str:
        try:
            subprocess.Popen(
                ["firefox", "--new-tab", "https://vk.com/audios"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return "🌐 Открываю VK Music"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    @staticmethod
    def _extract_query(text: str) -> str:
        query = text
        for word in ("найди", "поиск", "музыку", "музыка", "песню", "песня",
                     "трек", "вк", "вконтакте"):
            query = query.replace(word, "")
        return query.strip()


__all__ = ["AgentVKMusic"]
