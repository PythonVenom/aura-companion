"""
Машинка 01: Слух (AgentListener) — T-one streaming через sherpa-onnx.

Мигрирован из agents/listener.py (монолит, копия в Фазе 1).
Логика listen() переписана в Фазе 3.1:
- Streaming-цикл с endpoint detection (recognizer.is_endpoint)
- Ранний выход по тишине (0.8 сек после речи)
- reset(s) после endpoint — не склеиваем фразы
- Один create_stream на вызов (не батч в конце)

Это фикс дублей T-one (проблема 3 из ADR-002):
«аура который час аура которыйч» → «который час».

Что НЕ менялось:
- __init__ (загрузка T-one)
- _audio_callback
- get_stream
- execute
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
                dtype="int16",
                blocksize=1600,
                callback=self._audio_callback,
            )
            self.stream.start()
        return self.stream

    def listen(self, timeout=6):
        """
        Слушать микрофон до endpoint, тишины или таймаута.

        Возвращает строку (распознанный текст) или None.

        Streaming-режим: один create_stream, декодирование по фреймам,
        endpoint detection — возвращаем сразу, не ждём 6 сек.
        """
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

            # Один streaming-объект на весь вызов
            s = self.recognizer.create_stream()
            left_padding = self.np.zeros(2400, dtype=self.np.float32)
            s.accept_waveform(self.sample_rate, left_padding)

            start = time.time()
            last_voice_ts = None          # когда последний раз видели текст
            silence_after_voice = 0.0     # сколько секунд тишины после речи
            last_text = ""                # последний текст модели
            last_text_change_ts = None    # когда текст менялся последний раз
            TEXT_STABLE_SECONDS = 1.5     # Bug 34: было 0.6 — обрезал длинные фразы
            SILENCE_FALLBACK = 2.0        # Bug 34: было 1.2

            while time.time() - start < timeout:
                try:
                    data = self.audio_queue.get(timeout=0.2)
                except queue.Empty:
                    data = None

                if data is not None:
                    chunk = data.astype(self.np.float32).flatten() / 32768.0
                    s.accept_waveform(self.sample_rate, chunk)
                    while self.recognizer.is_ready(s):
                        self.recognizer.decode_stream(s)

                text_now = self.recognizer.get_result(s).strip().lower()

                # Обновляем таймстамп изменения текста модели.
                # T-one дописывает последнее слово через 0.3-0.5 сек после
                # окончания звука — ждём именно стабильности текста,
                # а не тишины в микрофоне.
                if text_now != last_text:
                    last_text = text_now
                    last_text_change_ts = time.time()

                if text_now:
                    if last_voice_ts is None:
                        last_voice_ts = time.time()
                    silence_after_voice = 0.0
                elif last_voice_ts is not None:
                    silence_after_voice = time.time() - last_voice_ts

                # Эндпоинт: модель сама говорит «фраза закончена»
                if self.recognizer.is_endpoint(s):
                    text = self.recognizer.get_result(s).strip().lower()
                    self.recognizer.reset(s)
                    if text and len(text) > 2:
                        print(f"🎤 Распознано: {text}")
                        return text
                    last_voice_ts = None
                    silence_after_voice = 0.0
                    last_text = ""
                    last_text_change_ts = None
                    continue

                # Основной выход: текст модели стабилен TEXT_STABLE_SECONDS.
                if (last_text and last_text_change_ts is not None
                        and (time.time() - last_text_change_ts) >= TEXT_STABLE_SECONDS
                        and len(last_text) > 2):
                    print(f"🎤 Распознано (стабильно): {last_text}")
                    return last_text

                # Fallback: 1.2с тишины в микрофоне (если модель не даёт текст).
                if last_voice_ts is not None and silence_after_voice >= SILENCE_FALLBACK:
                    text = self.recognizer.get_result(s).strip().lower()
                    if text and len(text) > 2:
                        print(f"🎤 Распознано (тишина): {text}")
                        return text
                    last_voice_ts = None
                    silence_after_voice = 0.0
                    last_text = ""
                    last_text_change_ts = None

            # Таймаут: отдаём то, что успели распознать
            tail_padding = self.np.zeros(4800, dtype=self.np.float32)
            s.accept_waveform(self.sample_rate, tail_padding)
            while self.recognizer.is_ready(s):
                self.recognizer.decode_stream(s)
            text = self.recognizer.get_result(s).strip().lower()
            if text and len(text) > 2:
                print(f"🎤 Распознано (таймаут): {text}")
                return text
            return None
        except Exception as e:
            print(f"⚠️ Ошибка распознавания: {e}")
            return None

    def execute(self, command):
        return self.listen()
