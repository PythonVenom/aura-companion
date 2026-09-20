"""
Машинка 02: Голос (AgentSpeaker)
"""

import os
import queue
import threading
import time
import subprocess
from agents.base import MicroAgent


class AgentSpeaker(MicroAgent):
    def __init__(self):
        super().__init__("speaker", "Голос Ауры")
        self.voice_path = os.path.expanduser("~/aura_project/voices/ru_RU-irina-medium.onnx")
        self.piper_cmd = os.path.expanduser("~/.local/bin/piper")
        self.aplay_process = None
        self.speech_queue = queue.Queue()
        self.is_speaking = False

    def say(self, text):
        if not self.active:
            return "🔇 Голос выключен"

        self.speech_queue.put(text)

        if not self.is_speaking:
            self.is_speaking = True
            threading.Thread(target=self._speak_worker, daemon=True).start()

        return f"🗣️ Сказала: {text[:50]}..."

    def _speak_worker(self):
        self.is_speaking = True
        while not self.speech_queue.empty():
            text = self.speech_queue.get()
            try:
                text = self._make_text_smart(text)

                if os.path.exists(self.piper_cmd) and os.path.exists(self.voice_path):
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                        f.write(text)
                        text_file = f.name

                    wav_file = f"/tmp/aura_speech_{int(time.time())}_{threading.get_ident()}.wav"
                    subprocess.run([self.piper_cmd, '-m', self.voice_path, '-i', text_file, '-f', wav_file], capture_output=True)
                    self.aplay_process = subprocess.Popen(
                        ['paplay', wav_file],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.aplay_process.wait()
                    os.unlink(text_file)
                    try:
                        os.unlink(wav_file)
                    except:
                        pass
                else:
                    subprocess.Popen(['espeak-ng', '-v', 'ru', '-p', '60', '-s', '160', text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"❌ Ошибка озвучивания: {e}")
        self.is_speaking = False

    def _make_text_smart(self, text):
        if 'создатель' not in text.lower():
            if len(text) < 50:
                text = f"{text}, Создатель"
        if text.endswith('.'):
            text = text[:-1] + '...'
        text = text.replace("аура", "Аура").replace("создатель", "Создатель")
        return text

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
