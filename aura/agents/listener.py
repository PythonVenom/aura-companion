import os
import subprocess
import time
import numpy as np
import sherpa_onnx
from aura.core.system_profiler import SystemProfiler

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../sherpa-onnx-streaming-t-one-russian-2025-09-08")

class AgentListener:
    def __init__(self):
        self.sample_rate = 16000
        self.ready = True
        self.recognizer = None
        self.stream = None
        self._process = None
        print("DEBUG: [Listener] Инициализация T-one...")

    def _init_model(self):
        if self.recognizer is not None:
            return
        tokens = os.path.join(MODEL_DIR, "tokens.txt")
        model = os.path.join(MODEL_DIR, "model.onnx")
        self.recognizer = sherpa_onnx.OnlineRecognizer.from_t_one_ctc(
            tokens=tokens,
            model=model,
            num_threads=1,
            sample_rate=self.sample_rate,
            feature_dim=80,
            decoding_method="greedy_search",
        )
        self.stream = self.recognizer.create_stream()
        print("DEBUG: [Listener] T-one загружен (16000 Hz).")

    def listen(self, timeout=6):
        try:
            self._init_model()
        except Exception as e:
            print(f"❌ Ошибка загрузки T-one: {e}")
            return None

        self.stream = self.recognizer.create_stream()
        
        # Читаем напрямую с железа (ID 72)
        mic = SystemProfiler.get_default_mic()
        cmd = ["parec", f"--device={mic}", "--rate=16000", "--channels=1", "--format=s16le"]
        if self._process is None or self._process.poll() is not None:
            self._process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        start_time = time.time()
        result_text = None
        
        try:
            while time.time() - start_time < timeout:
                data = self._process.stdout.read(3200)
                if not data:
                    break
                
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                self.stream.accept_waveform(self.sample_rate, samples)
                while self.recognizer.is_ready(self.stream):
                    self.recognizer.decode_stream(self.stream)
                
                if self.recognizer.is_endpoint(self.stream):
                    result_text = self.recognizer.get_result(self.stream)
                    self.recognizer.reset(self.stream)
                    if result_text:
                        break
        finally:
            # Процесс parec не убиваем, он живет постоянно
            pass
        
        if not result_text:
            self.stream.accept_waveform(self.sample_rate, np.zeros(int(0.5*self.sample_rate), dtype=np.float32))
            while self.recognizer.is_ready(self.stream):
                self.recognizer.decode_stream(self.stream)
            result_text = self.recognizer.get_result(self.stream)
            
        return result_text if result_text else None

    def close(self):
        if self._process:
            self._process.terminate()
            self._process = None
