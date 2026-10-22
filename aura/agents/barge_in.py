import subprocess
import threading
import time
import webrtcvad
import os

class AgentBargeIn:
    def __init__(self):
        # 2 - средняя агрессивность VAD (1 - низкая, 3 - высокая)
        self.vad = webrtcvad.Vad(2)
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
        print("✅ BargeIn (pw-record) запущен")
        return True

    def _listen_loop(self):
        # Читаем сырой звук с дефолтного (или 70) устройства через pw-record
        # Формат: 16000 Hz, 1 канал, s16 (2 байта на сэмпл)
        cmd = ["pw-record", "--rate", "16000", "--channels", "1", "--format", "s16", "-"]
        
        try:
            self._process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.DEVNULL
            )
            
            while self.running:
                # Читаем ВСЕГДА, чтобы буфер не забивался старым звуком
                data = self._process.stdout.read(640)
                if not data:
                    break
                
                if len(data) == 640 and self._is_aura_speaking:
                    try:
                        if self.vad.is_speech(data, 16000):
                            print("👂 [Barge-in] Обнаружена речь! Останавливаю Aura.")
                            if self.on_speech:
                                self.on_speech()
                            self._is_aura_speaking = False # Сброс после срабатывания
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

    def stop(self):
        self.running = False
        if self._process:
            self._process.terminate()
