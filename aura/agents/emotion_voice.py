"""T052 — эмоции по голосу.

Наука:
- Prosody features: pitch (F0), energy (RMS), speech rate, pauses
- Scherer 2003, Schuller 2013 (INTERSPEECH Emotion Challenge)
- Классификация: calm / sad / anxious / angry / neutral
"""
from __future__ import annotations
import math
import shutil
import subprocess
import tempfile
import os
import wave
import struct

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


class AgentEmotionVoice(MicroAgent):
    name = "emotion_voice"

    TRIGGERS = ("эмоци", "настроени", "как я звучу", "голос грустн",
                "голос злой", "устал по голосу")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if "статус" in t or "готов" in t:
            return self._status()
        if "послушай" in t or "проверь" in t or "анализ" in t:
            return self._analyze()
        return AgentResponse.ok(
            text="Эмоции по голосу. Скажи 'послушай меня 5 секунд'.",
            agent_name=self.name,
        )

    def _status(self) -> AgentResponse:
        has = shutil.which("arecord") is not None
        return AgentResponse.ok(
            text=f"🎙️ Анализ эмоций: {'готов' if has else 'нужен arecord (alsa-utils)'}.",
            agent_name=self.name,
        )

    def _record(self, seconds: int = 5) -> bytes | None:
        if not shutil.which("arecord"):
            return None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                path = f.name
            subprocess.run(
                ["arecord", "-q", "-f", "S16_LE", "-r", "16000",
                 "-c", "1", "-d", str(seconds), path],
                timeout=seconds + 5, check=False,
            )
            with open(path, "rb") as f:
                data = f.read()
            os.unlink(path)
            return data
        except Exception:
            return None

    def _features(self, wav_bytes: bytes) -> dict | None:
        """Простые prosody-признаки: RMS, zero-crossing rate, паузы."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav_bytes)
                path = f.name
            wf = wave.open(path, "rb")
            n = wf.getnframes()
            rate = wf.getframerate()
            raw = wf.readframes(n)
            wf.close()
            os.unlink(path)

            samples = struct.unpack(f"<{n}h", raw)
            if not samples:
                return None

            # RMS energy (нормировано)
            sum_sq = sum(s * s for s in samples)
            rms = math.sqrt(sum_sq / len(samples)) / 32768.0

            # Zero-crossing rate (прокси для «резкости»)
            zc = sum(1 for i in range(1, len(samples))
                     if (samples[i - 1] >= 0) != (samples[i] >= 0))
            zcr = zc / len(samples)

            # Паузы: фреймы с RMS < 20% от среднего
            frame = rate // 10  # 100мс
            frames = [samples[i:i + frame] for i in range(0, len(samples) - frame, frame)]
            frame_rms = []
            for fr in frames:
                if not fr:
                    continue
                fr_sq = sum(s * s for s in fr)
                frame_rms.append(math.sqrt(fr_sq / len(fr)))
            if frame_rms:
                avg = sum(frame_rms) / len(frame_rms)
                threshold = avg * 0.2
                silent = sum(1 for r in frame_rms if r < threshold)
                silence_ratio = silent / len(frame_rms)
            else:
                silence_ratio = 1.0

            # Простой прокси темпа: кол-во "слогов" = пиков выше avg*1.5
            peaks = 0
            for i in range(1, len(frame_rms) - 1):
                if frame_rms[i] > frame_rms[i - 1] and frame_rms[i] > frame_rms[i + 1]:
                    if frame_rms[i] > avg * 1.5:
                        peaks += 1
            duration = n / rate
            speech_rate = peaks / duration if duration > 0 else 0

            return {
                "rms": rms,
                "zcr": zcr,
                "silence_ratio": silence_ratio,
                "speech_rate": speech_rate,
                "duration": duration,
            }
        except Exception:
            return None

    def _classify(self, f: dict) -> tuple[str, str]:
        """Простой rule-based классификатор. Возвращает (эмоция, причина)."""
        rms = f["rms"]
        zcr = f["zcr"]
        silence = f["silence_ratio"]
        rate = f["speech_rate"]

        # Тишина = нет голоса
        if rms < 0.01 or silence > 0.85:
            return "тишина", "нет голоса / микрофон не слышит"

        # Тревожно: высокий ZCR + быстрый темп + короткие паузы
        if zcr > 0.15 and rate > 3.0 and silence < 0.4:
            return "тревожно", "резкий голос, быстрый темп"

        # Злобно: очень громко + резко
        if rms > 0.15 and zcr > 0.18:
            return "злобно", "громко и резко"

        # Грустно: тихо + медленно + много пауз
        if rms < 0.03 and rate < 1.5 and silence > 0.5:
            return "грустно", "тихо, медленно, паузы"

        # Устал: тихо + средний темп
        if rms < 0.04 and rate < 2.5:
            return "устало", "тихий ровный голос"

        # Спокойно: средний RMS, низкий ZCR
        if zcr < 0.1 and 0.03 < rms < 0.12:
            return "спокойно", "ровный голос"

        return "нейтрально", f"rms={rms:.2f}, zcr={zcr:.2f}, silence={silence:.2f}"

    def _analyze(self) -> AgentResponse:
        wav = self._record(5)
        if not wav:
            return AgentResponse.ok(
                text="⚠️ Нет arecord (alsa-utils).",
                agent_name=self.name,
            )
        feats = self._features(wav)
        if not feats:
            return AgentResponse.ok(
                text="⚠️ Не смогла разобрать звук.",
                agent_name=self.name,
            )
        emotion, reason = self._classify(feats)
        return AgentResponse.ok(
            text=f"🎙️ Настроение: **{emotion}** ({reason}).",
            agent_name=self.name,
        )
