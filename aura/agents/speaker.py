"""
Машинка 02: Голос (AgentSpeaker).

Копия agents/speaker.py для модульной архитектуры (Strangler Fig, Фаза 1).
Изменена ОДНА строка: импорт MicroAgent — теперь из aura.agents.base,
а не из agents.base.

Логика НЕ менялась. Известные баги монолита (гонка is_speaking, эхо
при быстром опустошении очереди) НЕ чинятся здесь — отдельная задача.
"""

import os
import queue
import threading
import time
import subprocess
from aura.agents.base import MicroAgent


class AgentSpeaker(MicroAgent):
    def __init__(self):
        super().__init__("speaker", "Голос Ауры")
        self.voice_path = os.path.expanduser("~/aura_project/voices/ru_RU-irina-medium.onnx")
        self.piper_cmd = os.path.expanduser("~/.local/bin/piper")
        self.aplay_process = None
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self._worker = None
        self._worker_lock = threading.Lock()

    def say(self, text):
        if not self.active:
            return "🔇 Голос выключен"

        self.speech_queue.put(text)

        # Bug 10 fix: worker жив? иначе запустить. Не полагаемся на
        # is_speaking — между queue.empty() и is_speaking=False есть окно.
        with self._worker_lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(
                    target=self._speak_worker, daemon=True)
                self._worker.start()

        return f"🗣️ Сказала: {text[:50]}..."

    def _speak_worker(self):
        """Вечный воркер: блокирующий get(timeout). Не выходит сам.

        Bug 10 fix v2: раньше `while not empty()` завершался, say()
        создавал второй worker → два paplay = троение.
        """
        while True:
            try:
                text = self.speech_queue.get(timeout=0.5)
            except queue.Empty:
                self.is_speaking = False
                continue
            if text is None:
                break
            self.is_speaking = True
            try:
                text = self._make_text_smart(text)
                if os.path.exists(self.piper_cmd) and os.path.exists(self.voice_path):
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                        f.write(text)
                        text_file = f.name
                    wav_file = f"/tmp/aura_speech_{int(time.time())}_{threading.get_ident()}.wav"
                    _vs = self._get_voice_settings()
                    _speed = _vs["speed"]
                    _cmd = [self.piper_cmd, '-m', self.voice_path, '-i', text_file, '-f', wav_file]
                    if _speed != 1.0:
                        _cmd.extend(["--length_scale", str(1.0 / _speed)])
                    subprocess.run(_cmd, capture_output=True)
                    self.aplay_process = subprocess.Popen(
                        ['paplay', wav_file],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.aplay_process.wait()
                    os.unlink(text_file)
                    try:
                        os.unlink(wav_file)
                    except Exception:
                        pass
                else:
                    subprocess.Popen(
                        ['espeak-ng', '-v', 'ru', '-p', '60', '-s', '160', text],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"❌ Ошибка озвучивания: {e}")

    def _get_voice_settings(self):
        """Получить настройки голоса из settings."""
        try:
            from aura import settings as _s
            return {
                "voice": _s.get("tts_voice", "ru_RU-irina-medium"),
                "speed": float(_s.get("tts_speed", 1.0)),
                "volume": int(_s.get("volume", 100)),
            }
        except Exception:
            return {"voice": "ru_RU-irina-medium", "speed": 1.0, "volume": 100}

    def _make_text_smart(self, text):
        if 'создатель' not in text.lower():
            if len(text) < 50:
                text = f"{text}, Создатель"
        if text.endswith('.'):
            text = text[:-1] + '...'
        text = text.replace("аура", "Аура").replace("создатель", "Создатель")
        return text

    def shutdown(self) -> None:
        """Graceful shutdown: остановить воркер и процессы."""
        self.speech_queue.put(None)   # сигнал воркеру выйти
        if hasattr(self, '_worker') and self._worker:
            self._worker.join(timeout=2.0)
        if self.aplay_process:
            try:
                self.aplay_process.terminate()
                self.aplay_process.wait(timeout=1.0)
            except Exception:
                pass
            self.aplay_process = None

    def stop_speaking(self):
        if self.aplay_process:
            self.aplay_process.terminate()
            self.aplay_process = None
            self.speech_queue.queue.clear()
            self.is_speaking = False
            return True
        return False

    def execute(self, command):
        return self.say(command)
