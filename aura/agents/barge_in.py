"""
Barge-in: перебивание Ауры.

Сервис (не BaseAgent). Как brain, tool_router.
Свой InputStream (16 kHz), VAD webrtcvad в фоне.
Когда Аура говорит и пользователь заговорил — callback.

Архитектура: ADR-006 (Уровень 3 — отдельный поток).
Не трогает listener. Один общий ALSA-микрофон.

Состояние: "слушаю всегда", но callback — только когда
`aura_speaking=True`.
"""

from __future__ import annotations

import queue
import threading
import time


class AgentBargeIn:
    """
    Детектор речи для barge-in.

    Публичные методы:
    - start(on_speech): запустить фоновый VAD
    - stop(): остановить
    - set_aura_speaking(bool): Аура говорит — VAD активен
    """

    SAMPLE_RATE = 16000
    FRAME_DURATION_MS = 30
    FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480
    VAD_AGGRESSIVENESS = 3            # было 2, ужесточили после AEC
    MIN_RMS = 4000                    # Bug 45 v3: эхо < 2000, речь рядом > 4000
    QUEUE_MAXSIZE = 50
    GATE_SECONDS = 4.0                # Bug 29: 2.5с (было 1.0) — ждём пока AEC устаканится
    MIN_SPEECH_FRAMES = 20  # Bug 45: 0.6с подряд            # Bug 29: 300мс подряд (было 3=90мс) — не ловим эхо
    COOLDOWN_SECONDS = 5.0  # Bug 45: 5с между            # Bug 29: не дёргать callback чаще 2с (было 0.5)

    def __init__(self):
        self.ready = False
        self.vad = None
        self.sd = None
        self.stream = None
        self.audio_queue = None
        self.thread = None
        self.running = False
        self.aura_speaking = False
        self.on_speech = None
        self._last_speech_ts = 0.0
        self._cooldown = self.COOLDOWN_SECONDS  # Bug 29: 2.0с
        self._speaking_started = 0.0  # когда Аура начала говорить
        self._consecutive_speech = 0  # счётчик фреймов речи подряд

        try:
            import webrtcvad
            import sounddevice as sd
            self.sd = sd
            self.vad = webrtcvad.Vad(self.VAD_AGGRESSIVENESS)
            self.ready = True
            print("✅ BargeIn загружен (VAD webrtcvad, отдельный поток)")
        except Exception as e:
            print(f"⚠️ BargeIn ошибка: {e}")
            self.ready = False

    def start(self, on_speech=None) -> bool:
        """Запустить фоновый VAD. on_speech — callback при речи."""
        if not self.ready:
            return False
        if self.running:
            return True

        self.on_speech = on_speech
        self.audio_queue = queue.Queue(maxsize=self.QUEUE_MAXSIZE)
        self.running = True

        def callback(indata, frames, time_info, status):
            if not self.running:
                return
            try:
                self.audio_queue.put_nowait(bytes(indata))
            except queue.Full:
                pass  # отбрасываем старые

        try:
            self.stream = self.sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=self.FRAME_SIZE,
                callback=callback,
            )
            self.stream.start()
        except Exception as e:
            print(f"⚠️ BargeIn stream error: {e}")
            self.running = False
            return False

        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def stop(self) -> None:
        """Остановить VAD и закрыть поток."""
        self.running = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None

    def set_aura_speaking(self, value: bool) -> None:
        """Аура говорит — VAD активен (callback сработает).

        При включении: запоминаем время старта (для gate) и сбрасываем
        счётчик подряд идущих фреймов речи.
        """
        if value and not self.aura_speaking:
            self._speaking_started = time.time()
            self._consecutive_speech = 0
        self.aura_speaking = value

    def _loop(self) -> None:
        """Фоновый цикл: читает фреймы, VAD, callback."""
        while self.running:
            try:
                frame = self.audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if not self.aura_speaking:
                continue

            # Gate: не дёргать callback первые GATE_SECONDS после старта речи.
            # AEC вычитает эхо с задержкой ~20 мс — на старте эхо ещё в микрофоне.
            if time.time() - self._speaking_started < self.GATE_SECONDS:
                continue

            if len(frame) != self.FRAME_SIZE * 2:
                continue

            # Bug 45: RMS-гейт — эхо от колонок тише речи пользователя
            import numpy as _np
            _samples = _np.frombuffer(frame, dtype=_np.int16).astype(_np.float32)
            _rms = int(_np.sqrt(_np.mean(_samples * _samples))) if len(_samples) else 0
            if _rms < self.MIN_RMS:
                self._consecutive_speech = 0
                # Bug 45 v2: лог для калибровки (первые 5 срабатываний)
                if getattr(self, "_rms_logs", 0) < 5 and _rms > 500:
                    print(f"🔇 RMS {_rms} < {self.MIN_RMS} (эхо)")
                    self._rms_logs = getattr(self, "_rms_logs", 0) + 1
                continue

            try:
                is_speech = self.vad.is_speech(frame, self.SAMPLE_RATE)
            except Exception:
                continue

            # Счётчик: нужно MIN_SPEECH_FRAMES подряд. Одиночные всплески
            # (остатки эха, щелчки) не считаются.
            if not is_speech:
                self._consecutive_speech = 0
                continue

            self._consecutive_speech += 1
            if self._consecutive_speech < self.MIN_SPEECH_FRAMES:
                continue

            now = time.time()
            if now - self._last_speech_ts < self._cooldown:
                continue
            self._last_speech_ts = now
            self._consecutive_speech = 0  # сбросили после срабатывания

            if self.on_speech is not None:
                try:
                    self.on_speech()
                except Exception as e:
                    print(f"⚠️ BargeIn callback error: {e}")


__all__ = ["AgentBargeIn"]
