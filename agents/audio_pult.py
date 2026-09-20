"""
Машинка 15: Аудио-пульт (AgentAudioPult)
"""

import re
import subprocess
from agents.base import MicroAgent


class AgentAudioPult(MicroAgent):
    def __init__(self):
        super().__init__("audio_pult", "Аудио-пульт")
        self.ready = True
        self.player = "vlc"

        self.digit_words = {
            'один': 1, 'одна': 1, 'одну': 1, 'одного': 1, 'одному': 1,
            'два': 2, 'две': 2, 'двух': 2, 'двум': 2,
            'три': 3, 'трех': 3, 'трёх': 3, 'трем': 3, 'трём': 3,
            'четыре': 4, 'четыр': 4, 'четырех': 4, 'четырёх': 4,
            'пять': 5, 'пяти': 5, 'пятер': 5,
            'шесть': 6, 'шести': 6, 'шестер': 6,
            'семь': 7, 'семи': 7, 'семер': 7,
            'восемь': 8, 'восьми': 8, 'восьмер': 8,
            'девять': 9, 'девяти': 9, 'девятер': 9,
            'десять': 10, 'десяти': 10, 'десятер': 10
        }

    def execute(self, command):
        cmd = command.lower()

        numbers = re.findall(r'\b(10|[1-9])\b', cmd)
        if numbers:
            target = int(numbers[0]) * 10
            return self._set_volume(target)

        for word, num in self.digit_words.items():
            if word in cmd:
                target = num * 10
                return self._set_volume(target)

        if any(word in cmd for word in ['прибавь', 'плюс', 'добавь', 'увеличь', 'громче']):
            for word, num in self.digit_words.items():
                if word in cmd:
                    return self._change_volume_by(num * 10)
            if numbers:
                return self._change_volume_by(int(numbers[0]) * 10)
            return self._change_volume_by(10)

        if any(word in cmd for word in ['убавь', 'минус', 'сделай меньше', 'тише', 'меньше']):
            for word, num in self.digit_words.items():
                if word in cmd:
                    return self._change_volume_by(-num * 10)
            if numbers:
                return self._change_volume_by(-int(numbers[0]) * 10)
            return self._change_volume_by(-10)

        if 'выключи звук' in cmd or 'звук на ноль' in cmd:
            return self._mute()
        if 'включи звук' in cmd:
            return self._unmute()

        if 'включи' in cmd or 'запусти' in cmd or 'плей' in cmd:
            if 'музык' in cmd or 'песн' in cmd or 'трек' in cmd:
                return self._play_music()
            if 'радио' in cmd:
                return self._play_radio()
            return self._play_music()
        elif 'выключи' in cmd or 'стоп' in cmd:
            return self._control_player("stop")
        elif 'пауза' in cmd:
            return self._control_player("pause")
        elif 'следующ' in cmd or 'переключи' in cmd or 'вперёд' in cmd:
            return self._control_player("next")
        elif 'предыдущ' in cmd or 'назад' in cmd:
            return self._control_player("previous")

        return "🎵 Не поняла команду. Попробуй: громкость 1-10, прибавь громкость, уменьши громкость"

    def _get_current_volume(self):
        try:
            result = subprocess.run(['pactl', 'get-sink-volume', '@DEFAULT_SINK@'], capture_output=True, text=True)
            return int(result.stdout.split()[4].strip('%'))
        except:
            return 50

    def _set_volume(self, target_percent):
        try:
            target_percent = max(0, min(100, target_percent))
            subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{target_percent}%'], check=False)
            return f"🔊 Громкость установлена на {target_percent // 10} из 10 ({target_percent}%)"
        except:
            return "🔊 Не удалось установить громкость"

    def _change_volume_by(self, delta_percent):
        try:
            current = self._get_current_volume()
            target = max(0, min(100, current + delta_percent))
            subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{target}%'], check=False)
            return f"🔊 Громкость: {target // 10} из 10 ({target}%)"
        except:
            return "🔊 Не удалось изменить громкость"

    def _mute(self):
        try:
            subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '1'], check=False)
            return "🔇 Звук выключен"
        except:
            return "🔇 Не удалось выключить звук"

    def _unmute(self):
        try:
            subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '0'], check=False)
            return "🔊 Звук включен"
        except:
            return "🔊 Не удалось включить звук"

    def _play_music(self):
        try:
            result = subprocess.run(['playerctl', 'play'], capture_output=True, text=True)
            if result.returncode == 0:
                return "🎵 Включаю музыку!"
            else:
                subprocess.Popen(['vlc', '--play-and-exit', '~/Music/'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "🎵 Запускаю VLC с музыкой!"
        except:
            return "🎵 Не удалось запустить музыку"

    def _play_radio(self):
        try:
            subprocess.Popen(['vlc', 'http://icecast.radiofrance.fr/franceculture-hifi.aac'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "📻 Включаю радио!"
        except:
            return "📻 Не удалось включить радио"

    def _control_player(self, action):
        try:
            result = subprocess.run(['playerctl', action], capture_output=True, text=True)
            if result.returncode == 0:
                actions = {"play": "▶️", "stop": "⏹️", "pause": "⏸️", "next": "⏭️", "previous": "⏮️"}
                return f"{actions.get(action, '🔄')} Выполнила: {action}"
            else:
                return "🎵 Не нашла активный плеер. Запусти музыку вручную."
        except:
            return "🎵 Не удалось управлять плеером."
