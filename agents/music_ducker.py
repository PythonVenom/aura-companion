"""
Машинка 61: Приглушение источника (AgentMusicDucker)
"""

import subprocess
from agents.base import MicroAgent


class AgentMusicDucker(MicroAgent):
    def __init__(self):
        super().__init__("music_ducker", "Приглушение всех источников")
        self.ready = True
        self.active_sink_inputs = {}

    def _get_all_active_sink_inputs(self):
        try:
            result = subprocess.run(['pactl', 'list', 'short', 'sink-inputs'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            streams = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) > 0:
                        streams.append(parts[0])
            return streams
        except:
            return []

    def _get_sink_input_volume(self, sink_input_id):
        try:
            result = subprocess.run(['pactl', 'get-sink-input-volume', sink_input_id], capture_output=True, text=True)
            return int(result.stdout.split()[4].strip('%'))
        except:
            return 100

    def duck(self):
        sink_inputs = self._get_all_active_sink_inputs()
        if not sink_inputs:
            return "🔇 Нет активного фонового звука."
        self.active_sink_inputs = {}
        for sid in sink_inputs:
            vol = self._get_sink_input_volume(sid)
            self.active_sink_inputs[sid] = vol
            subprocess.run(['pactl', 'set-sink-input-volume', sid, '20%'], check=False)
        return f"🔉 Приглушила {len(sink_inputs)} источников до 20%. Слушаю тебя."

    def un_duck(self):
        if not self.active_sink_inputs:
            return "🔇 Нет сохраненных источников для восстановления."
        for sid, vol in self.active_sink_inputs.items():
            try:
                subprocess.run(['pactl', 'set-sink-input-volume', sid, f'{vol}%'], check=False)
            except:
                pass
        self.active_sink_inputs = {}
        return "🔊 Восстановила фоновый звук."

    def execute(self, command):
        if 'приглуши' in command or 'тише' in command:
            return self.duck()
        elif 'восстанови' in command or 'громче' in command or 'верни' in command:
            return self.un_duck()
        return "Приглушение готово. Скажи: приглуши все, восстанови звук"
