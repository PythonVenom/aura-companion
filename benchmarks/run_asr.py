#!/usr/bin/env python3
"""ASR: T-one streaming CTC, замер распознавания WAV.

T-one — streaming CTC, sample_rate=8000. Piper выдаёт 22050 — нужен resample.
"""
import sys
import time
import wave
from pathlib import Path

import numpy as np
import sherpa_onnx

MODEL_DIR = Path.home() / "aura_project" / "sherpa-onnx-streaming-t-one-russian-2025-09-08"
TARGET_SR = 8000


def load_wav_any_sr(path):
    """Загрузить WAV любой частоты, вернуть (samples float32, sample_rate)."""
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n_ch = w.getnchannels()
        frames = w.readframes(w.getnframes())
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if n_ch == 2:
        audio = audio.reshape(-1, 2).mean(axis=1)
    return audio, sr


def resample(audio, src_sr, dst_sr):
    if src_sr == dst_sr:
        return audio
    n_out = int(len(audio) * dst_sr / src_sr)
    idx = np.linspace(0, len(audio) - 1, n_out)
    return np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)


def main():
    wav = sys.argv[1] if len(sys.argv) > 1 else "/tmp/aura_tts_bench.wav"
    wav_path = Path(wav)
    if not wav_path.exists():
        print(f"WAV not found: {wav}")
        sys.exit(1)

    print("## ASR (T-one streaming CTC)")
    print("")
    print("```")

    # Загрузка модели
    t0 = time.perf_counter()
    recognizer = sherpa_onnx.OnlineRecognizer.from_t_one_ctc(
        model=str(MODEL_DIR / "model.onnx"),
        tokens=str(MODEL_DIR / "tokens.txt"),
        num_threads=2,
        sample_rate=TARGET_SR,
        decoding_method="greedy_search",
    )
    load_ms = (time.perf_counter() - t0) * 1000
    print(f"model load: {load_ms:.0f} ms")

    audio, sr = load_wav_any_sr(wav_path)
    if sr != TARGET_SR:
        audio = resample(audio, sr, TARGET_SR)
        print(f"resampled: {sr} Hz -> {TARGET_SR} Hz")

    audio_ms = len(audio) / TARGET_SR * 1000
    print(f"audio: {audio_ms:.0f} ms")

    stream = recognizer.create_stream()
    t0 = time.perf_counter()
    stream.accept_waveform(TARGET_SR, audio)
    stream.input_finished()
    while recognizer.is_ready(stream):
        recognizer.decode_stream(stream)
    text = recognizer.get_result(stream)
    infer_ms = (time.perf_counter() - t0) * 1000

    print(f"inference: {infer_ms:.0f} ms")
    print(f"RTF: {infer_ms / audio_ms:.3f} (real-time factor)")
    print(f"text: {text!r}")
    print("```")


if __name__ == "__main__":
    main()
