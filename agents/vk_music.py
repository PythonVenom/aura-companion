"""
Машинка 69: VK Музыка (AgentVKMusic)
"""

import os
import subprocess
from agents.base import MicroAgent


try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


class AgentVKMusic(MicroAgent):
    def __init__(self):
        super().__init__("vk_music", "Музыка ВКонтакте")
        self.token = None
        self.last_track = None
        self.last_track_id = None
        self._load_token()

    def _load_token(self):
        paths = [
            "vk_token.txt",
            os.path.expanduser("~/aura_project/vk_token.txt"),
            os.path.expanduser("~/vk_token.txt"),
            "./vk_token.txt"
        ]

        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        self.token = f.read().strip()
                    if self.token and len(self.token) > 10:
                        print(f"✅ VK токен загружен ({len(self.token)} символов)")
                        return True
                except:
                    pass

        print("⚠️ VK токен не найден. Создайте vk_token.txt")
        return False

    def _vk_request(self, method, params):
        if not REQUESTS_OK:
            return {'error': 'requests не установлен'}

        if not self.token:
            return {'error': 'Токен не найден'}

        try:
            params['access_token'] = self.token
            params['v'] = '5.131'
            url = f"https://api.vk.com/method/{method}"
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def play(self):
        if not self.token:
            return "❌ VK токен не найден"

        try:
            result = self._vk_request('audio.getRecommendations', {'count': 5})

            if 'error' in result:
                err = result['error']
                if isinstance(err, dict) and err.get('error_code') == 5:
                    return "❌ Токен истёк. Получите новый на vkhost.github.io"
                return f"❌ Ошибка VK: {err}"

            items = result.get('response', {}).get('items', [])
            if not items:
                return "❌ Нет рекомендаций. Попробуйте 'найди [исполнитель]'"

            track = items[0]
            self.last_track = track
            self.last_track_id = track.get('id')

            artist = track.get('artist', 'Неизвестный')
            title = track.get('title', 'Без названия')

            track_url = f"https://vk.com/audio{track.get('owner_id')}_{track.get('id')}"
            subprocess.Popen(['firefox', '--new-tab', track_url],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            return f"🎵 Включаю: {artist} - {title}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def search_track(self, query):
        if not self.token:
            return "❌ Токен не найден"
        if not query:
            return "❌ Что искать?"

        try:
            result = self._vk_request('audio.search', {
                'q': query,
                'count': 5,
                'sort': 2
            })

            if 'error' in result:
                return f"❌ Ошибка VK: {result['error']}"

            items = result.get('response', {}).get('items', [])
            if not items:
                return f"❌ Ничего не найдено по '{query}'"

            track = items[0]
            self.last_track = track
            self.last_track_id = track.get('id')

            artist = track.get('artist', 'Неизвестный')
            title = track.get('title', 'Без названия')

            track_url = f"https://vk.com/audio{track.get('owner_id')}_{track.get('id')}"
            subprocess.Popen(['firefox', '--new-tab', track_url],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            return f"🎵 Нашла: {artist} - {title}"
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"

    def add_to_playlist(self):
        if not self.token:
            return "❌ Токен не найден"
        if not self.last_track:
            return "❌ Нет трека. Сначала 'включи музыку' или 'найди [запрос]'"

        try:
            track_id = self.last_track.get('id')
            owner_id = self.last_track.get('owner_id')

            if not track_id or not owner_id:
                return "❌ Неверные данные трека"

            result = self._vk_request('audio.add', {
                'audio_id': track_id,
                'owner_id': owner_id
            })

            if 'error' in result:
                return f"❌ Ошибка VK: {result['error']}"

            if 'response' in result:
                return f"✅ Добавлено в плейлист: {self.last_track.get('title')}"
            return "❌ Не удалось добавить"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def like_track(self):
        if not self.token:
            return "❌ Токен не найден"
        if not self.last_track:
            return "❌ Нет трека. Сначала 'включи музыку' или 'найди [запрос]'"

        try:
            track_id = self.last_track.get('id')
            owner_id = self.last_track.get('owner_id')

            if not track_id or not owner_id:
                return "❌ Неверные данные трека"

            result = self._vk_request('audio.setLike', {
                'audio_id': track_id,
                'owner_id': owner_id,
                'like': 1
            })

            if 'error' in result:
                return f"❌ Ошибка VK: {result['error']}"

            if 'response' in result:
                return f"❤️ Лайк: {self.last_track.get('title')}"
            return "❌ Не удалось поставить лайк"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def execute(self, command):
        cmd = command.lower()

        if 'найди' in cmd or 'поиск' in cmd:
            query = cmd
            for word in ['найди', 'поиск', 'музыку', 'музыка', 'песню', 'песня', 'трек']:
                query = query.replace(word, '')
            query = query.strip()
            return self.search_track(query)

        if 'включи' in cmd and ('музык' in cmd or 'песн' in cmd):
            return self.play()

        if 'добавь' in cmd and ('плейлист' in cmd or 'песн' in cmd or 'трек' in cmd):
            return self.add_to_playlist()

        if 'лайк' in cmd or 'нравится' in cmd:
            return self.like_track()

        if 'открой вк' in cmd or 'открой музыку' in cmd:
            subprocess.Popen(['firefox', '--new-tab', 'https://vk.com/audios'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "🌐 Открываю VK Music"

        return "🎵 Команды: включи музыку, найди Radiohead, лайк, добавь песню"
