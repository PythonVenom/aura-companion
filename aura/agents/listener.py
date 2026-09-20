"""
Машинка 01: Слух (AgentListener) — T-one streaming через sherpa-onnx.

Копия agents/listener.py для модульной архитектуры (Strangler Fig, Фаза 1).
Изменена ОДНА строка: импорт MicroAgent — теперь из aura.agents.base,
а не из agents.base.

Логика НЕ менялась. Тесты должны быть идентичны монолиту.
"""

import os
import queue
import time
from aura.agents.base import MicroAgent


class AgentListener(MicroAgent):
    def __init__(self):
        super().__init__("listener", "Слух Ауры")
        self.ready = False
        self.recognizer = None
        self.stream = None
        self.audio_queue = None
        self.sample_rate = 8000

        try:
            import sherpa_onnx
            import sounddevice as sd
            import numpy as np
            self.sd = sd
            self.np = np

            model_dir = os.path.expanduser("~/aura_project/sherpa-onnx-streaming-t-one-russian-2025-09-08")
            model = os.path.join(model_dir, "model.onnx")
            tokens = os.path.join(model_dir, "tokens.txt")

            if not all(os.path.exists(p) for p in [model, tokens]):
                print("⚠️ Не найдены файлы T-one")
                return

            self.recognizer = sherpa_onnx.OnlineRecognizer.from_t_one_ctc(
                model=model,
                tokens=tokens,
                num_threads=2,
                sample_rate=self.sample_rate,
                decoding_method="greedy_search",
            )
            self.ready = True
            print("✅ T-one загружен (streaming)")
        except Exception as e:
            print(f"⚠️ Ошибка T-one: {e}")
            self.ready = False

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"⚠️ Audio status: {status}")
        if self.audio_queue is not None:
            self.audio_queue.put(indata.copy())

    def get_stream(self):
        if self.stream is None and self.ready:
            self.audio_queue = queue.Queue()
            self.stream = self.sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=1600,
                callback=self._audio_callback,
            )
            self.stream.start()
        return self.stream

    def listen(self, timeout=6):
        if not self.ready or not self.active:
            return None
        try:
            stream = self.get_stream()
            if not stream:
                return None

            # Сброс буфера — убираем старые данные
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break

            frames = []
            start = time.time()
            while time.time() - start < timeout:
                try:
                    data = self.audio_queue.get(timeout=0.5)
                    frames.append(data)
                except queue.Empty:
                    pass

            if not frames:
                return None

            audio_data = self.np.concatenate(frames).astype(self.np.float32).flatten() / 32768.0
            print(f"🎤 Записано: {len(audio_data)} сэмплов ({len(audio_data)/self.sample_rate:.1f} сек)")

            s = self.recognizer.create_stream()
            left_padding = self.np.zeros(2400, dtype=self.np.float32)
            s.accept_waveform(self.sample_rate, left_padding)
            s.accept_waveform(self.sample_rate, audio_data)
            tail_padding = self.np.zeros(4800, dtype=self.np.float32)
            s.accept_waveform(self.sample_rate, tail_padding)
            s.input_finished()

            while self.recognizer.is_ready(s):
                self.recognizer.decode_stream(s)

            text = self.recognizer.get_result(s).strip().lower()
            if text and len(text) > 2:
                return text
            return None
        except Exception as e:
            print(f"⚠️ Ошибка распознавания: {e}")
            return None

    def execute(self, command):
        return self.listen()
