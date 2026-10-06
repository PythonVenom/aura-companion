"""
Агент поиска и воспроизведения медиа.

Сканирует папки с музыкой и фильмами. Находит по запросу. Открывает в VLC/mpv.

По науке:
- Изолирован (os, subprocess)
- Тестируем (mock для subprocess, temp-папки для сканирования)
- Не знает про AuraCore
- Воспроизведение — mock в тестах
"""

from __future__ import annotations

import os
import subprocess
from difflib import get_close_matches

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentMediaSearch(BaseAgent):
    """
    Агент поиска медиа.

    Обрабатывает:
    - "найди музыку X" / "включи песню X" → play music
    - "включи фильм X" → play movie
    - "список музыки" / "какая музыка" → list music
    - "список фильмов" → list movies
    - "пересканируй медиа" → rescan
    - "стоп" / "останови музыку" → stop
    """

    name = "media_search"

    FIND_KEYWORDS = ("найди музыку", "найди песню", "найди фильм",
                     "включи музыку", "включи песню", "включи фильм",
                     "поставь музыку", "поставь песню", "поставь фильм",
                     "включи трек", "поставь трек")
    LIST_MUSIC_KEYWORDS = ("список музыки", "какая музыка", "вся музыка", "список треков")
    LIST_MOVIE_KEYWORDS = ("список фильмов", "какие фильмы", "все фильмы")
    RESCAN_KEYWORDS = ("пересканируй медиа", "пересканируй музыку", "обнови медиа")
    STOP_KEYWORDS = ("стоп музыка", "останови музыку", "стоп трек", "выключи музыку")

    DEFAULT_MOVIE_DIRS = [
        os.path.expanduser("~/Movies"),
        os.path.expanduser("~/Видео"),
        "/mnt/aura_hdd/media",
        "/mnt/aura_hdd/movies",
        "/mnt/aura_hdd/video",
    ]
    DEFAULT_MUSIC_DIRS = [
        os.path.expanduser("~/Music"),
        os.path.expanduser("~/Музыка"),
        "/mnt/aura_hdd/music",
        "/mnt/aura_hdd/audio",
    ]

    def __init__(
        self,
        movie_dirs: list[str] | None = None,
        music_dirs: list[str] | None = None,
    ) -> None:
        super().__init__()
        # F-009: media_dirs/music_dirs из settings с fallback на DEFAULT_*
        if movie_dirs is not None:
            self.movie_dirs = movie_dirs
        elif music_dirs is not None:
            self.movie_dirs = self.DEFAULT_MOVIE_DIRS
        else:
            try:
                from aura import settings as _s
                custom_media = _s.get("media_dirs", [])
                custom_music = _s.get("music_dirs", [])
                self.movie_dirs = list(custom_media) or self.DEFAULT_MOVIE_DIRS
                self.music_dirs = list(custom_music) or self.DEFAULT_MUSIC_DIRS
            except Exception:
                self.movie_dirs = self.DEFAULT_MOVIE_DIRS
                self.music_dirs = self.DEFAULT_MUSIC_DIRS
        if music_dirs is not None:
            self.music_dirs = music_dirs
        self.video_ext = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v', '.wmv')
        self.audio_ext = ('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.opus', '.wma')
        self.media_cache: dict[str, list[dict]] = {"movies": [], "music": []}
        self._scan()

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        keywords = (
            self.FIND_KEYWORDS
            + self.LIST_MUSIC_KEYWORDS
            + self.LIST_MOVIE_KEYWORDS
            + self.RESCAN_KEYWORDS
            + self.STOP_KEYWORDS
        )
        return any(kw in text for kw in keywords)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.RESCAN_KEYWORDS):
            return AgentResponse.ok(self.rescan(), self.name)

        if any(kw in text for kw in self.STOP_KEYWORDS):
            return AgentResponse.ok(self.stop_media(), self.name)

        if any(kw in text for kw in self.LIST_MUSIC_KEYWORDS):
            return AgentResponse.ok(self.list_music(), self.name)

        if any(kw in text for kw in self.LIST_MOVIE_KEYWORDS):
            return AgentResponse.ok(self.list_movies(), self.name)

        if any(kw in text for kw in self.FIND_KEYWORDS):
            query = self._extract_query(text)
            if not query:
                return AgentResponse.ok("Что включить?", self.name)
            kind = "movie" if "фильм" in text else "music"
            return AgentResponse.ok(self.play_media(query, kind), self.name)

        return AgentResponse.not_handled(self.name)

    # --- Сканирование ---

    def _scan(self) -> None:
        for d in self.movie_dirs:
            if os.path.exists(d):
                self._scan_dir(d, self.media_cache["movies"], self.video_ext)
        for d in self.music_dirs:
            if os.path.exists(d):
                self._scan_dir(d, self.media_cache["music"], self.audio_ext)

    def _scan_dir(self, path: str, result: list, extensions: tuple) -> None:
        try:
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.lower().endswith(extensions):
                        full_path = os.path.join(root, f)
                        result.append({
                            "name": os.path.splitext(f)[0],
                            "file": full_path,
                            "title": os.path.splitext(f)[0],
                        })
        except Exception:
            pass

    # --- Поиск ---

    def find_media(self, query: str, kind: str = "both") -> dict | None:
        if kind == "movie":
            pool = self.media_cache["movies"]
        elif kind == "music":
            pool = self.media_cache["music"]
        else:
            pool = self.media_cache["movies"] + self.media_cache["music"]

        if not pool:
            return None

        query_lower = query.lower().strip()
        if not query_lower:
            return None

        # Точное вхождение
        for m in pool:
            if query_lower in m["title"].lower():
                return m

        # Нечёткий поиск
        titles = [m["title"] for m in pool]
        matches = get_close_matches(query_lower, [t.lower() for t in titles], n=1, cutoff=0.5)
        if matches:
            for m in pool:
                if m["title"].lower() == matches[0]:
                    return m
        return None

    # --- Действия ---

    def play_media(self, query: str, kind: str = "both") -> str:
        media = self.find_media(query, kind)
        if not media:
            return f"❌ Не нашла: {query}"

        # Flatpak VLC vs native
        try:
            subprocess.Popen(
                ["vlc", "--play-and-exit", media["file"]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"🎵 Включаю: {media['title']}"
        except FileNotFoundError:
            pass

        try:
            subprocess.Popen(
                ["mpv", media["file"]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"🎵 Включаю: {media['title']}"
        except FileNotFoundError:
            return "❌ Ни VLC, ни mpv не найдены"

    def stop_media(self) -> str:
        try:
            subprocess.run(["pkill", "-x", "vlc"], check=False, capture_output=True)
            subprocess.run(["pkill", "-x", "mpv"], check=False, capture_output=True)
            return "⏹️ Остановила воспроизведение"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def list_music(self, filter_text: str = "") -> str:
        music = self.media_cache["music"]
        if filter_text:
            music = [m for m in music if filter_text.lower() in m["title"].lower()]
        if not music:
            return "❌ Музыка не найдена"
        out = [f"🎵 Треков: {len(music)}"]
        for i, m in enumerate(music[:20], 1):
            out.append(f"{i}. {m['title']}")
        if len(music) > 20:
            out.append(f"... и ещё {len(music) - 20}")
        return "\n".join(out)

    def list_movies(self, filter_text: str = "") -> str:
        movies = self.media_cache["movies"]
        if filter_text:
            movies = [m for m in movies if filter_text.lower() in m["title"].lower()]
        if not movies:
            return "❌ Фильмы не найдены"
        out = [f"🎬 Фильмов: {len(movies)}"]
        for i, m in enumerate(movies[:20], 1):
            out.append(f"{i}. {m['title']}")
        if len(movies) > 20:
            out.append(f"... и ещё {len(movies) - 20}")
        return "\n".join(out)

    def rescan(self) -> str:
        self.media_cache = {"movies": [], "music": []}
        self._scan()
        return (
            f"🔄 Пересканировала: фильмов {len(self.media_cache['movies'])}, "
            f"музыки {len(self.media_cache['music'])}"
        )

    @staticmethod
    def _extract_query(text: str) -> str:
        """Извлечь запрос из 'включи музыку X'."""
        for prefix in ("найди музыку", "найди песню", "найди фильм",
                       "включи музыку", "включи песню", "включи фильм",
                       "поставь музыку", "поставь песню", "поставь фильм",
                       "включи трек", "поставь трек"):
            if prefix in text:
                query = text.split(prefix, 1)[1].strip()
                return query
        return ""


__all__ = ["AgentMediaSearch"]
