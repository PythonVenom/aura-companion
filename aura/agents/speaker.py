"""
Машинка 02: Голос (AgentSpeaker).

Копия agents/speaker.py для модульной архитектуры (Strangler Fig, Фаза 1).
Изменена ОДНА строка: импорт MicroAgent — теперь из aura.agents.base,
а не из agents.base.

Логика НЕ менялась. Известные баги монолита (гонка is_speaking, эхо
при быстром опустошении очереди) НЕ чинятся здесь — отдельная задача.
"""

import contextlib
import os
import queue
import subprocess
import threading
import time

from aura.agents.base import MicroAgent


class AgentSpeaker(MicroAgent):
    def __init__(self):
        self._speak_lock = threading.Lock()
        super().__init__("speaker", "Голос Ауры")
        self.activate()
        # AURA_VOICE_XDG_FIX_V3: XDG в приоритете (project/models/voices — пустая)
        from pathlib import Path as _P
        _xdg = _P.home() / ".local/share/aura/voices"
        _proj = __import__("aura.paths", fromlist=["MODELS_DIR"]).MODELS_DIR / "voices"
        _voice_dir = _xdg if _xdg.exists() else _proj
        self.voice_path = str(_voice_dir / "ru_RU-irina-medium.onnx")
        import shutil
        self.piper_cmd = shutil.which("piper") or os.path.expanduser("~/.local/bin/piper")
        self.aplay_process = None
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self._worker = None
        self._worker_lock = threading.Lock()
        self._ducker = None   # Bug 32: lazy ducker (ducking при речи)

    def _get_ducker(self):
        """Bug 32: lazy-инициализация ducking (приглушение всего кроме Aura)."""
        if self._ducker is None:
            try:
                from aura.agents.music_ducker import AgentMusicDucker
                self._ducker = AgentMusicDucker()
            except Exception:
                self._ducker = False  # не смог — отключаем
        return self._ducker

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

    def wait(self, timeout=10.0):
        """Блокирует, пока очередь не опустеет и paplay не доиграет."""
        import time as _t
        deadline = _t.monotonic() + timeout
        while _t.monotonic() < deadline:
            if self.speech_queue.empty() and not self.is_speaking:
                break
            _t.sleep(0.1)
        if self.aplay_process and self.aplay_process.poll() is None:
            with contextlib.suppress(Exception):
                self.aplay_process.wait(timeout=5)

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
            ducked = False
            try:
                text = self._make_text_smart(text)
                # Bug 32: приглушить всё (музыка, браузер) кроме Aura
                ducker = self._get_ducker()
                if ducker:
                    try:
                        ducker.duck()
                        ducked = True
                    except Exception as e:
                        import logging
                        logging.getLogger('aura.speaker').debug(
                            'duck error: %s', e)
                # FIX: сброс флага после речи
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
                    subprocess.run(_cmd, capture_output=True, timeout=15)
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
                    pass # espeak removed
            except Exception as e:
                print(f"❌ Ошибка озвучивания: {e}")
            finally:
                # Bug 32: восстановить громкость
                if ducked and ducker:
                    try:
                        ducker.un_duck()
                    except Exception as e:
                        import logging
                        logging.getLogger('aura.speaker').debug(
                            'un_duck error: %s', e)
                self.is_speaking = False  # >>> AURA_HANG_FIX_V1

    def _voice_for_lang(self) -> str:
        """Голос piper для текущего языка i18n. ta — fallback en."""
        _map = {
            "ru": "ru_RU-irina-medium",
            "en": "en_US-amy-medium",
            "de": "de_DE-thorsten-medium",
            "hi": "hi_IN-priyamvada-medium",
            "ja": "ja_JP-hi_fi_captain-medium",
            "ko": "ko_KO-kss-medium",
        }
        try:
            from aura.i18n import get_lang
            lang = get_lang()
        except Exception:
            lang = "ru"
        if lang not in _map:
            import logging
            logging.getLogger(__name__).warning("TTS: no voice for lang=%s, fallback en", lang)
            lang = "en"
        return _map[lang]

    def _sync_voice_path(self, voice_name: str) -> None:
        try:
            import os as _os

            # AURA_VOICE_XDG_FIX_V2: тот же fallback что в __init__
            from pathlib import Path as _P2

            from aura.paths import MODELS_DIR
            _proj2 = MODELS_DIR / "voices"
            _xdg2 = _P2.home() / ".local/share/aura/voices"
            _dir2 = _proj2 if _proj2.exists() else _xdg2
            vp = str(_dir2 / f"{voice_name}.onnx")
            if _os.path.exists(vp):
                self.voice_path = vp
        except Exception:
            pass

    def _get_voice_settings(self):
        try:
            from aura import settings as _s
            base_vol = int(_s.get("volume", 100))
            boost = float(_s.get("voice_volume_boost", 1.0))
            boosted = min(100, int(base_vol * boost))
            voice_name = _s.get("tts_voice") or self._voice_for_lang()
            self._sync_voice_path(voice_name)
            return {
                "voice": voice_name,
                "speed": float(_s.get("tts_speed", 1.0)),
                "volume": boosted,
            }
        except Exception:
            voice_name = self._voice_for_lang()
            self._sync_voice_path(voice_name)
            return {"voice": voice_name, "speed": 1.0, "volume": 100}

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
        suffix = persona.get("honorific", "") if address == "вы" else ""

        if suffix and suffix.lower() not in text.lower() and len(text) < 50:
            text = f"{text}, {suffix}"
        if text.endswith('.'):
            text = text[:-1] + '...'
        text = text.replace("аура", "Аура").replace("создатель", "Создатель")
        return text


    def stop(self) -> None:
        """Принудительно остановить воспроизведение (Barge-in)."""
        # 1. Очищаем очередь от всего, что еще не началось
        with self.speech_queue.mutex:
            self.speech_queue.queue.clear()
            
        # 2. Убиваем плеер (pw-play/aplay), если он сейчас играет
        if hasattr(self, 'aplay_process') and self.aplay_process:
            try:
                self.aplay_process.terminate()
                self.aplay_process = None
                print("🛑 [Barge-in] Воспроизведение остановлено пользователем.")
            except Exception:
                pass

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
