"""Aura Voice Bridge — Vosk слушает, Aura выполняет."""
import json, os, queue, sys, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sounddevice as sd
import vosk
from src.demon import Aura
from src.aura_control import AuraControl, handle

import subprocess as _sp

def speak(text):
    """Озвучивает текст через espeak-ng (русский)."""
    if not text or not isinstance(text, str):
        return
    clean = "".join(c for c in text if c.isprintable() or c.isspace())
    clean = clean.replace("°C", "градусов").replace("₽", "рублей")
    clean = clean.replace("+", "плюс ").replace("#", "")
    try:
        # Piper TTS — нейросеть, живой голос Ирины
        SPEAKING[0] = True
        try:
            p1 = _sp.Popen(
                ["piper", "-m", os.path.expanduser("~/aura_project/models/piper/ru_RU-irina-medium.onnx"),
                 "-f", "/tmp/aura_voice.wav"],
                stdin=_sp.PIPE, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL
            )
            p1.communicate(input=clean.encode("utf-8"))
            _sp.run(["aplay", "-q", "/tmp/aura_voice.wav"], check=False)
        finally:
            import time as _t
            _t.sleep(2.0)
            SPEAKING[0] = False
    except Exception as e:
        print(f"[tts] Ошибка: {e}")


MODEL_PATH = os.path.expanduser("~/aura_project/models/vosk-ru")
SAMPLE_RATE = 16000
SPEAKING = [False]
STOP_WORDS = ["стоп аура", "аура стоп", "выход", "пока аура"]


class VoiceAura:
    def __init__(self):
        if not os.path.isdir(MODEL_PATH):
            raise RuntimeError(f"Модель не найдена: {MODEL_PATH}")
        vosk.SetLogLevel(-1)
        self.model = vosk.Model(MODEL_PATH)
        self.rec = vosk.KaldiRecognizer(self.model, SAMPLE_RATE)
        self.q = queue.Queue()
        self.aura = Aura()
        self.control = AuraControl(self.aura)
        self.running = False
        self.last_cmd_time = 0

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[voice] {status}", file=sys.stderr)
        self.q.put(bytes(indata))

    def process_phrase(self, text):
        text = text.lower().strip()
        if not text:
            return
        if time.time() - self.last_cmd_time < 1.5:
            return
        # Пропускаем если Aura сейчас говорит
        if SPEAKING[0]:
            # Очищаем буфер — Vosk не должен запоминать голос Aura
            while not self.q.empty():
                try:
                    self.q.get_nowait()
                except Exception:
                    break
            return
        self.last_cmd_time = time.time()
        print(f"\n🎤 УСЛЫШАЛА: «{text}»")
        if any(sw in text for sw in STOP_WORDS):
            print("👋 Стоп. Выхожу.")
            self.running = False
            return
        cmd = text.replace("аура,", "").replace("аура", "").strip()
        if not cmd:
            return
        try:
            result = handle(self.aura, cmd)
            print(f"🤖 Аура: {result}")
            speak(result)
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def listen_forever(self):
        self.running = True
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                               dtype="int16", channels=1, callback=self._callback):
            print("=" * 60)
            print("🎤 Aura Voice — СЛУШАЮ ПОСТОЯННО")
            print("=" * 60)
            print("Говори: «Аура, <команда>»")
            print("Примеры: 'Аура, сколько времени', 'Аура, погода'")
            print("Стоп: «Аура стоп» или Ctrl+C")
            print("=" * 60)
            while self.running:
                data = self.q.get()
                if self.rec.AcceptWaveform(data):
                    text = json.loads(self.rec.Result()).get("text", "").strip()
                    if text:
                        self.process_phrase(text)


if __name__ == "__main__":
    try:
        va = VoiceAura()
        va.listen_forever()
    except KeyboardInterrupt:
        print("\n[voice] Остановлено.")
    except Exception as e:
        print(f"[voice] Ошибка: {e}")
