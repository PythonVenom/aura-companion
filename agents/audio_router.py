"""
Агент аудио-маршрутизации.
Определяет, что подключено: jack, USB, Bluetooth.
Автоматически переключает вход и выход.
"""

import subprocess

from .base import MicroAgent


class AgentAudioRouter(MicroAgent):
    def __init__(self):
        super().__init__("audio_router", "Аудио-маршрутизатор")
        self.ready = True
        self.current_profile = None
        self.current_source = None
        self.current_sink = None
        self.last_check = 0
        self.check_interval = 5

        self.detect_and_route()

    def _run_pactl(self, args):
        try:
            result = subprocess.run(
                ['pactl'] + args,
                capture_output=True, text=True, timeout=3
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _get_active_port(self, source_or_sink, name):
        try:
            result = subprocess.run(
                ['pactl', 'list', source_or_sink],
                capture_output=True, text=True, timeout=3
            )
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if name in line:
                    for j in range(i, min(i + 40, len(lines))):
                        if 'Active Port:' in lines[j]:
                            return lines[j].split(':', 1)[1].strip()
            return None
        except Exception:
            return None

    def _detect_profile(self):
        """
        Определяет профиль по активному ПОРТУ ВЫХОДА.
        headphones = jack вставлен, speaker = jack вынут.
        """
        try:
            output_port = self._get_active_port('sinks', 'alsa_output')

            if output_port:
                if 'analog-output-headphones' in output_port:
                    return "headset"
                elif 'analog-output-speaker' in output_port:
                    return "internal"

            result = self._run_pactl(['list', 'sources', 'short'])
            if 'usb' in result.lower():
                return "usb"
            if 'bluez' in result.lower():
                return "bluetooth"

            return "unknown"
        except Exception:
            return "unknown"

    def _set_default_source(self, name):
        try:
            subprocess.run(['pactl', 'set-default-source', name],
                           capture_output=True, timeout=3)
            return True
        except Exception:
            return False

    def _set_default_sink(self, name):
        try:
            subprocess.run(['pactl', 'set-default-sink', name],
                           capture_output=True, timeout=3)
            return True
        except Exception:
            return False

    def _fix_speaker_volume(self):
        """
        Поднимает Speaker на 100%, если он упал в 0.
        Нужно для Realtek ALC1220, который обнуляет Speaker
        при переключении профиля.
        """
        subprocess.run(
            ['pactl', 'set-sink-volume',
             'alsa_output.pci-0000_00_1f.3.analog-stereo', '100%'],
            capture_output=True, timeout=3
        )

    def detect_and_route(self):
        profile = self._detect_profile()
        old_profile = self.current_profile
        self.current_profile = profile

        if old_profile == profile:
            return (profile, None)

        if profile in ("headset", "internal"):
            source = "alsa_input.pci-0000_00_1f.3.analog-stereo"
            sink = "alsa_output.pci-0000_00_1f.3.analog-stereo"
            self._set_default_source(source)
            self._set_default_sink(sink)
            self.current_source = source
            self.current_sink = sink
            self._fix_speaker_volume()

            if profile == "headset":
                return (profile, "🎧 Обнаружена гарнитура. Слушаю через микрофон, говорю в наушники.")
            else:
                return (profile, "🔊 Гарнитура отключена. Использую встроенные микрофон и динамики.")

        elif profile == "usb":
            self._fix_speaker_volume()
            return (profile, "🎙️ Обнаружено USB-аудио. Использую его.")

        elif profile == "bluetooth":
            self._fix_speaker_volume()
            return (profile, "📡 Обнаружено Bluetooth-аудио. Использую его.")

        return (profile, "🔧 Аудио-маршрутизация обновлена.")

    def get_status(self):
        return {
            "profile": self.current_profile,
            "source": self.current_source,
            "sink": self.current_sink
        }

    def check_and_route(self):
        import time as t
        now = t.time()
        if now - self.last_check < self.check_interval:
            return None
        self.last_check = now

        profile, message = self.detect_and_route()
        if message:
            speaker = self._get_speaker()
            if speaker:
                speaker.say(message)
            return message
        return None

    def _get_speaker(self):
        import __main__
        aura = getattr(__main__, 'aura', None)
        if aura and hasattr(aura, 'agents'):
            return aura.agents.get('speaker')
        return None

    def execute(self, command):
        cmd = command.lower()

        if 'проверь аудио' in cmd or 'аудио статус' in cmd:
            status = self.get_status()
            return f"🎧 Аудио: {status['profile']}\nВход: {status['source']}\nВыход: {status['sink']}"

        elif 'переключи аудио' in cmd:
            self.current_profile = None
            profile, message = self.detect_and_route()
            return message or "🔧 Аудио-маршрутизация обновлена."

        elif 'какая гарнитура' in cmd or 'что подключено' in cmd:
            profile = self._detect_profile()
            names = {
                "headset": "🎧 Гарнитура (jack)",
                "internal": "🔊 Встроенные (микрофон и динамики)",
                "usb": "🎙️ USB-аудио",
                "bluetooth": "📡 Bluetooth-аудио",
                "unknown": "❓ Неизвестно"
            }
            return names.get(profile, "❓ Неизвестно")

        return "🎧 Аудио-маршрутизатор готов. Команды: проверь аудио, какая гарнитура, переключи аудио"
