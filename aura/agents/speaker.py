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
import subprocess
import threading
import time

from aura.agents.base import MicroAgent


class AgentSpeaker(MicroAgent):
    def __init__(self):
        super().__init__("speaker", "Голос Ауры")
        self.activate()
        self.voice_path = str(__import__("aura.paths", fromlist=["MODELS_DIR"]).MODELS_DIR / "voices/ru_RU-irina-medium.onnx")
        import shutil
        self.piper_cmd = shutil.which("piper") or os.path.expanduser("~/.local/bin/piper")
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
                    # >>> AURA_HANG_FIX_V1
                    # Оценка длительности: WAV 22050 Hz mono 16-bit
                    try:
                        _secs = max(2.0, os.path.getsize(wav_file) / 44100.0)
                    except OSError:
                        _secs = 10.0
                    _timeout = _secs + 5.0
                    try:
                        self.aplay_process.wait(timeout=_timeout)
                    except subprocess.TimeoutExpired:
                        print(f'⚠️ paplay висит >{_timeout:.1f}s — kill')
                        try:
                            self.aplay_process.kill()
                            self.aplay_process.wait(timeout=1.0)
                        except Exception as e:
                            # F-006: не глотать (раздел 17 промта)
                            import logging
                            logging.getLogger('aura.speaker').debug(
                                'speaker error: %s', e)
                    finally:
                        os.unlink(text_file)
                        try:
                            os.unlink(wav_file)
                        except Exception as e:
                            # F-006: не глотать (раздел 17 промта)
                            import logging
                            logging.getLogger('aura.speaker').debug(
                                'speaker error: %s', e)
                else:
                    subprocess.Popen(
                        ['espeak-ng', '-v', 'ru', '-p', '60', '-s', '160', text],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"❌ Ошибка озвучивания: {e}")
            finally:
                self.is_speaking = False  # >>> AURA_HANG_FIX_V1

    def _get_voice_settings(self):
        """Получить настройки голоса из settings."""
        try:
            from aura import settings as _s
            # F-015: voice_volume_boost для elder-care (MANIFESTO.md)
            base_vol = int(_s.get("volume", 100))
            boost = float(_s.get("voice_volume_boost", 1.0))
            boosted = min(100, int(base_vol * boost))
            return {
                "voice": _s.get("tts_voice", "ru_RU-irina-medium"),
                "speed": float(_s.get("tts_speed", 1.0)),
                "volume": boosted,
            }
        except Exception:
            return {"voice": "ru_RU-irina-medium", "speed": 1.0, "volume": 100}

    def _make_text_smart(self, text):
        # >>> AURA_RUACCENT_V1
        # ruaccent: расстановка ударений перед TTS (Bug 51 — снятие «создатЭлЪ»)
        # AURA_RUACCENT_OFF_V1 — временно отключено (transformers 5.x)
        try:
            raise ImportError('ruaccent temporarily disabled')
            from ruaccent import RUAccent
            if not hasattr(self, "_accentizer"):
                self._accentizer = RUAccent()
                self._accentizer.load(omograph_model_size="turbo3.1",
                                      use_dictionary=True)
            text = self._accentizer.process_all(text)
        except Exception as _e:
            pass  # AURA_RUACCENT_QUIET_V1 — не шуметь

        try:
            from aura import settings as _s
            persona = _s.load().get("persona", {})
            address = persona.get("address", "ты")
            persona.get("style", "warm")
        except Exception:
            address, _style = "ты", "warm"

        # Обращение
        # >>> AURA_NO_ADDRESS_V1
        # Дефолт: address != "вы" → вокатив НЕ добавляется.
        # Elder care (backlog, дальняя полка): address == "вы" + persona.honorific.
        suffix = persona.get("honorific", "Создатель") if address == "вы" else ""

        if suffix and suffix.lower() not in text.lower() and len(text) < 50:
            text = f"{text}, {suffix}"
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
            except Exception as e:
                # F-006: не глотать (раздел 17 промта)
                import logging
                logging.getLogger('aura.speaker').debug(
                    'speaker error: %s', e)
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
