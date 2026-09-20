"""
Машинка Media: Поиск медиа (AgentMediaSearch)
Ищет фильмы и музыку в локальных папках, открывает в VLC/MPV.
"""

import os
import subprocess
from difflib import get_close_matches
from agents.base import MicroAgent


class AgentMediaSearch(MicroAgent):
    def __init__(self):
        super().__init__("media_search", "Поиск медиа")
        self.ready = True

        # Папки для поиска
        self.movie_dirs = [
            os.path.expanduser("~/Movies"),
            os.path.expanduser("~/Видео"),
            "/mnt/aura_hdd/media",
            "/mnt/aura_hdd/movies",
            "/mnt/aura_hdd/video",
        ]
        self.music_dirs = [
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Музыка"),
            "/mnt/aura_hdd/music",
            "/mnt/aura_hdd/audio",
        ]

        # Расширения
        self.video_ext = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v', '.wmv')
        self.audio_ext = ('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.opus', '.wma')

        self.media_cache = {"movies": [], "music": []}
        self._scan()

        print(f"✅ MediaSearch: фильмов {len(self.media_cache['movies'])}, музыки {len(self.media_cache['music'])}")

    def _scan(self):
        """Сканировать папки"""
        for d in self.movie_dirs:
            if os.path.exists(d):
                self._scan_dir(d, self.media_cache['movies'], self.video_ext)
        for d in self.music_dirs:
            if os.path.exists(d):
                self._scan_dir(d, self.media_cache['music'], self.audio_ext)

    def _scan_dir(self, path, result, extensions):
        """Рекурсивный обход папки"""
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
        except Exception as e:
            print(f"⚠️ Ошибка сканирования {path}: {e}")

    def find_media(self, query, kind="both"):
        """Найти медиа по имени (fuzzy)"""
        query_lower = query.lower().strip()
        if not query_lower:
            return None

        # Определяем, что искать
        if kind == "movie":
            pool = self.media_cache['movies']
        elif kind == "music":
            pool = self.media_cache['music']
        else:
            pool = self.media_cache['movies'] + self.media_cache['music']

        if not pool:
            return None

        # Точное совпадение
        for m in pool:
            if query_lower == m['name'].lower():
                return m

        # Частичное
        for m in pool:
            if query_lower in m['name'].lower():
                return m

        # Fuzzy
        names = [m['name'].lower() for m in pool]
        matches = get_close_matches(query_lower, names, n=1, cutoff=0.5)
        if matches:
            for m in pool:
                if m['name'].lower() == matches[0]:
                    return m

        return None

    def play_media(self, query, kind="both"):
        """Открыть медиа в VLC"""
        media = self.find_media(query, kind)
        if not media:
            return f"❌ Не нашла '{query}'"

        try:
            subprocess.Popen(
                ['vlc', '--play-and-exit', media['file']],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return f"▶️ Включаю: {media['name']}"
        except Exception as e:
            # Fallback — mpv
            try:
                subprocess.Popen(
                    ['mpv', media['file']],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                return f"▶️ Включаю (mpv): {media['name']}"
            except:
                return f"❌ Не удалось открыть: {e}"

    def list_movies(self, filter_text=""):
        """Список фильмов"""
        movies = self.media_cache['movies']
        if filter_text:
            filter_lower = filter_text.lower()
            movies = [m for m in movies if filter_lower in m['name'].lower()]

        if not movies:
            return f"📭 Фильмов не найдено"

        answer = f"🎬 Фильмов: {len(movies)}\n\n"
        for i, m in enumerate(movies[:30], 1):
            answer += f"{i}. {m['name'][:60]}\n"
        if len(movies) > 30:
            answer += f"\n... и ещё {len(movies) - 30}"
        return answer

    def list_music(self, filter_text=""):
        """Список музыки"""
        music = self.media_cache['music']
        if filter_text:
            filter_lower = filter_text.lower()
            music = [m for m in music if filter_lower in m['name'].lower()]

        if not music:
            return f"📭 Музыки не найдено"

        answer = f"🎵 Треков: {len(music)}\n\n"
        for i, m in enumerate(music[:30], 1):
            answer += f"{i}. {m['name'][:60]}\n"
        if len(music) > 30:
            answer += f"\n... и ещё {len(music) - 30}"
        return answer

    def stop_media(self):
        """Остановить VLC/mpv"""
        try:
            subprocess.run(['pkill', '-f', 'vlc'], check=False)
            subprocess.run(['pkill', '-f', 'mpv'], check=False)
            return "⏹️ Медиа остановлено"
        except:
            return "⏹️ Не удалось остановить"

    def rescan(self):
        """Пересканировать папки"""
        self.media_cache = {"movies": [], "music": []}
        self._scan()
        return f"🔄 Пересканировала: фильмов {len(self.media_cache['movies'])}, музыки {len(self.media_cache['music'])}"

    def execute(self, command):
        cmd = command.lower().strip()

        if 'пересканируй' in cmd or 'обнови медиа' in cmd:
            return self.rescan()

        if 'останови' in cmd and ('музык' in cmd or 'фильм' in cmd or 'видео' in cmd):
            return self.stop_media()

        if 'какие фильмы' in cmd or 'список фильмов' in cmd:
            filter_text = cmd.replace('какие фильмы', '').replace('список фильмов', '').strip()
            return self.list_movies(filter_text)

        if 'какая музыка' in cmd or 'список музыки' in cmd or 'какие песни' in cmd:
            filter_text = cmd.replace('какая музыка', '').replace('список музыки', '').replace('какие песни', '').strip()
            return self.list_music(filter_text)

        if 'включи фильм' in cmd:
            query = cmd.replace('включи фильм', '').strip()
            if not query:
                return "Какой фильм?"
            return self.play_media(query, "movie")

        if 'включи песню' in cmd or 'включи трек' in cmd or 'включи музыку' in cmd:
            query = cmd.replace('включи песню', '').replace('включи трек', '').replace('включи музыку', '').strip()
            if not query:
                return "Какую музыку?"
            return self.play_media(query, "music")

        if 'включи' in cmd:
            query = cmd.replace('включи', '').strip()
            if query:
                return self.play_media(query, "both")

        return "🎬 MediaSearch готов. Команды: включи фильм X, включи песню Y, какие фильмы"
