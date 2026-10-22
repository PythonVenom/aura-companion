import subprocess
import threading
import time
import webrtcvad
import os

class AgentBargeIn:
    def __init__(self):
        self.vad = webrtcvad.Vad(3)
        self.running = False
        self.ready = True
        self._thread = None
        self._process = None
        self.on_speech = None
        self._is_aura_speaking = False

    def start(self, on_speech=None) -> bool:
        if self.running:
            return True
        
        self.on_speech = on_speech
        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("✅ BargeIn (pw-record, target 72) запущен")
        return True

    def _listen_loop(self):
        # ИСПРАВЛЕНИЕ: Слушаем target 72 напрямую
        cmd = ["pw-record", "--target", "72", "--rate", "16000", "--channels", "1", "--format", "s16", "-"]
        
        try:
            self._process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.DEVNULL
            )
            
            while self.running:
                data = self._process.stdout.read(640)
                if not data:
                    break
                
                if len(data) == 640 and self._is_aura_speaking:
                    if time.time() - getattr(self, 'speak_start_time', 0) < 3.0: continue
                    try:
                        if self.vad.is_speech(data, 16000):
                            self.speech_frames = getattr(self, 'speech_frames', 0) + 1
                            if getattr(self, 'speech_frames', 0) > 50:  # Ждем 300 мс речи
                                print("👂 [Barge-in] Обнаружена речь! Останавливаю Aura.")
                            if self.on_speech:
                                self.on_speech()
                            self._is_aura_speaking = False
                    except Exception as e:
                        print(f"VAD error: {e}")
                        
        except Exception as e:
            print(f"⚠️ Barge-in stream error: {e}")
        finally:
            if self._process:
                self._process.terminate()
                self._process = None

    def set_aura_speaking(self, speaking: bool):
        self._is_aura_speaking = speaking
        if speaking: self.speak_start_time = time.time()

    def stop(self):
        self.running = False
        if self._process:
            self._process.terminate()
