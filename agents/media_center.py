"""
Машинка 24: Медиацентр (AgentMediaCenter)
"""

import subprocess
from agents.base import MicroAgent


class AgentMediaCenter(MicroAgent):
    def __init__(self):
        super().__init__("media", "Медиацентр")
        self.volume = 70
        self.current_source = None

    def execute(self, command):
        if 'продолжи' in command or 'продолжи музыку' in command:
            return self._resume_last_source()
        elif 'запусти' in command or 'включи' in command:
            return self._play(command)
        elif 'выключи' in command or 'стоп' in command:
            return self._stop()
        elif 'громче' in command:
            self.volume = min(100, self.volume + 10)
            return f"🔊 Громкость: {self.volume}%"
        elif 'тише' in command:
            self.volume = max(0, self.volume - 10)
            return f"🔉 Громкость: {self.volume}%"
        return "🎵 Медиацентр готов"

    def _resume_last_source(self):
        import __main__
        aura = getattr(__main__, 'aura', None)
        memory = aura.agents.get('context_memory') if aura else None
        if memory:
            last_source = memory.get_last_media_source()
            if last_source:
                self.current_source = last_source['process']
                if last_source['process'] == 'youtube':
                    return "🎵 Продолжаю YouTube в браузере (в фоне)"
                elif last_source['process'] == 'vlc':
                    return "🎵 Продолжаю VLC (без вызова на передний план)"
                elif last_source['process'] == 'spotify':
                    return "🎵 Продолжаю Spotify"
                else:
                    return f"🎵 Продолжаю текущий источник: {last_source['title'][:30]}"
        return "🎵 Не могу найти предыдущий источник"

    def _play(self, command):
        if 'youtube' in command or 'ютуб' in command:
            self.current_source = 'youtube'
            return "🎵 Запускаю YouTube (в фоне)"
        elif 'vlc' in command or 'плеер' in command:
            self.current_source = 'vlc'
            return "🎵 Запускаю VLC (в фоне)"
        else:
            import __main__
            aura = getattr(__main__, 'aura', None)
            memory = aura.agents.get('context_memory') if aura else None
            if memory:
                last = memory.get_last_media_source()
                if last:
                    self.current_source = last['process']
                    return f"🎵 Возвращаюсь к последнему источнику: {last['title'][:30]}"
            self.current_source = 'spotify'
            return "🎵 Запускаю Spotify"

    def _stop(self):
        try:
            subprocess.run(['playerctl', 'stop'], capture_output=True)
        except:
            pass
        return "⏹️ Музыка остановлена"
