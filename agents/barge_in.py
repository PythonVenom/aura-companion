"""
Машинка Barge-in: перебивание Ауры (AgentBargeIn)
Слушает микрофон через VAD, детектит речь поверх эха.
"""

import os
import queue
import threading
import time
from agents.base import MicroAgent


class AgentBargeIn(MicroAgent):
    def __init__(self):
        super().__init__("barge_in", "Перебивание")
        self.ready = False
        self.vad = None
        self.stream = None
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)

        try:
            import webrtcvad
            import sounddevice as sd
            import numpy as np
            self.sd = sd
            self.np = np
            self.vad = webrtcvad.Vad(2)  # 0-3, 2 — средняя агрессивность
            self.ready = True
            print("✅ BargeIn загружен (VAD webrtcvad)")
        except Exception as e:
            print(f"⚠️ BargeIn ошибка: {e}")
            self.ready = False

    def is_speech(self, duration=0.3):
        """Проверить, есть ли речь за duration секунд"""
        if not self.ready:
            return False

        try:
            num_frames = int(duration * 1000 / self.frame_duration)
            frames = []

            def callback(indata, frames_count, time_info, status):
                frames.append(bytes(indata))

            stream = self.sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.frame_size,
                dtype='int16',
                channels=1,
                callback=callback,
            )
            stream.start()
            time.sleep(duration)
            stream.stop()
            stream.close()

            # Проверяем VAD на каждом фрейме
            for frame in frames:
                if len(frame) == self.frame_size * 2:  # int16 = 2 байта
                    try:
                        if self.vad.is_speech(frame, self.sample_rate):
                            return True
                    except:
                        pass
            return False
        except Exception as e:
            return False

    def execute(self, command):
        return "BargeIn готов"


