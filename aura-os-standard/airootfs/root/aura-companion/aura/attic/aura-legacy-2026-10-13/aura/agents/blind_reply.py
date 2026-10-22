"""T048 — голосовой ответ на уведомление.

Наука:
- org.freedesktop.Notifications: Notify + ActionInvoked
- Vosk ASR (offline, RU) → распознать команду
- Ответ → NotifyClosed / action callback
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

VOSK_MODEL_PATHS = [
    os.path.expanduser("~/.cache/vosk/vosk-model-small-ru"),
    "/usr/share/vosk/vosk-model-small-ru",
    os.path.expanduser("~/.local/share/vosk/vosk-model-small-ru"),
]


class AgentBlindReply(MicroAgent):
    name = "blind_reply"

    TRIGGERS = ("ответь на уведомление", "голосовой ответ",
                "скажи в уведомление", "продиктуй ответ")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if "статус" in t:
            return self._status()
        if any(k in t for k in ("ответь", "продиктуй", "скажи")):
            return self._listen_and_reply()
        return AgentResponse.ok(
            text="T048: 'ответь на уведомление' — включу микрофон на 5 сек.",
            agent_name=self.name,
        )

    def _model_path(self) -> str | None:
        for p in VOSK_MODEL_PATHS:
            if os.path.isdir(p):
                return p
        return None

    def _status(self) -> AgentResponse:
        model = self._model_path()
        has_vosk = False
        try:
            import vosk  # noqa
            has_vosk = True
        except ImportError:
            pass
        return AgentResponse.ok(
            text=f"🎤 T048: vosk={'да' if has_vosk else 'нет'}, "
                 f"model={'есть' if model else 'нет'}.",
            agent_name=self.name,
        )

    def _record_5s(self) -> bytes | None:
        if not shutil.which("arecord"):
            return None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                path = f.name
            subprocess.run(
                ["arecord", "-q", "-f", "S16_LE", "-r", "16000",
                 "-c", "1", "-d", "5", path],
                timeout=8, check=False,
            )
            with open(path, "rb") as f:
                data = f.read()
            os.unlink(path)
            return data
        except Exception:
            return None

    def _asr(self, wav_bytes: bytes) -> str | None:
        model = self._model_path()
        if not model:
            return None
        try:
            import wave

            import vosk
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav_bytes)
                path = f.name
            wf = wave.open(path, "rb")
            rec = vosk.KaldiRecognizer(vosk.Model(model), wf.getframerate())
            out = []
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                if rec.AcceptWaveform(data):
                    out.append(json.loads(rec.Result()).get("text", ""))
            out.append(json.loads(rec.FinalResult()).get("text", ""))
            wf.close()
            os.unlink(path)
            return " ".join(x for x in out if x).strip()
        except Exception:
            return None

    def _send_notification(self, text: str) -> bool:
        if not shutil.which("notify-send"):
            return False
        try:
            subprocess.run(
                ["notify-send", "-a", "Aura", "Голосовой ответ", text],
                timeout=5, check=False,
            )
            return True
        except Exception:
            return False

    def _listen_and_reply(self) -> AgentResponse:
        if not self._model_path():
            return AgentResponse.ok(
                text="⚠️ Нет Vosk-модели. Скачай vosk-model-small-ru в ~/.cache/vosk/",
                agent_name=self.name,
            )
        wav = self._record_5s()
        if not wav:
            return AgentResponse.ok(
                text="⚠️ Нет arecord (пакет alsa-utils).",
                agent_name=self.name,
            )
        text = self._asr(wav)
        if not text:
            return AgentResponse.ok(
                text="🎤 Не разобрала. Попробуй ещё раз.",
                agent_name=self.name,
            )
        self._send_notification(text)
        return AgentResponse.ok(
            text=f"🎤 Ответ: «{text[:80]}»",
            agent_name=self.name,
        )
