"""Aura Voice — распознавание русской речи через Vosk (офлайн)."""
import contextlib
import json
import os
import queue
import sys
import time

import sounddevice as sd
import vosk

MODEL_PATH = os.path.expanduser("~/aura_project/models/vosk-ru")
SAMPLE_RATE = 16000


class VoiceListener:
    def __init__(self, model_path=MODEL_PATH):
        if not os.path.isdir(model_path):
            raise RuntimeError(f"Модель Vosk не найдена: {model_path}")
        vosk.SetLogLevel(-1)
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, SAMPLE_RATE)
        self.q = queue.Queue()
        self.running = False

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[voice] {status}", file=sys.stderr)
        self.q.put(bytes(indata))

    def listen(self, on_phrase, duration=None):
        self.running = True
        start = time.time()
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16",
            channels=1, callback=self._callback,
        ):
            print("[voice] Слушаю... (Ctrl+C для выхода)")
            while self.running:
                if duration and (time.time() - start) > duration:
                    break
                data = self.q.get()
                if self.rec.AcceptWaveform(data):
                    text = json.loads(self.rec.Result()).get("text", "").strip()
                    if text and on_phrase:
                        on_phrase(text)


def demo():
    def on_phrase(text):
        print(f"\n>>> РАСПОЗНАНО: {text}")
    v = VoiceListener()
    with contextlib.suppress(KeyboardInterrupt):
        v.listen(on_phrase, duration=30)
    print("\n[voice] Стоп.")


if __name__ == "__main__":
    demo()
