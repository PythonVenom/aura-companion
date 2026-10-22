import sys
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
        """Воркер: использует MMS-TTS (нейроголос Facebook, локально)."""
        import torch
        import soundfile as sf
        import uuid
        from transformers import VitsModel, AutoTokenizer
        
        print("DEBUG: [Worker] Загружаю MMS-TTS (нейроголос Meta)...")
        model_path = os.path.expanduser("~/.cache/huggingface/mms-tts-rus")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = VitsModel.from_pretrained(model_path)
            print("DEBUG: [Worker] MMS-TTS успешно загружен.")
        except Exception as e:
            print(f"❌ [Worker] Не удалось загрузить MMS-TTS: {e}")
            return

        while True:
            try:
                text = self.speech_queue.get(timeout=0.5)
            except queue.Empty:
                self.is_speaking = False
                continue
            if text is None:
                break
                
            self.is_speaking = True
            ducker = self._get_ducker()
            try:
                text = self._make_text_smart(text)
                if ducker:
                    try: ducker.duck()
                    except: pass

                print(f"DEBUG: [Worker] Генерирую речь через MMS-TTS...")
                inputs = tokenizer(text, return_tensors="pt")
                with torch.no_grad():
                    output = model(**inputs).waveform
                
                wav_file = f"/tmp/aura_speech_{uuid.uuid4().hex}.wav"
                audio = output.numpy().squeeze()
                sf.write(wav_file, audio, model.config.sampling_rate)
                print("DEBUG: [Worker] MMS-TTS сгенерировал WAV.")
                
                self.aplay_process = subprocess.Popen(
                    ['pw-play', wav_file],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self.aplay_process.wait()
                self.aplay_process = None
                print("DEBUG: [Worker] MMS-TTS отработал (pw-play).")
            except Exception as e:
                print(f"❌ [Worker] Speaker error: {type(e).__name__}: {e}")
            finally:
                if ducker:
                    try: ducker.unduck()
                    except: pass
                self.is_speaking = False

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
