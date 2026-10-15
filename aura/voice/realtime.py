"""Realtime API — единый поток голос+vision.

Наука: OpenAI Realtime, AV-HuBERT (Shi 2022).
Объединяет AgentListener (STT) + Camera + AgentFacialEmotion.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class RealtimeFrame:
    """Один кадр мультимодального потока."""
    audio_text: str = ""
    video_emotion: str = "neutral"
    video_faces: int = 0
    ts: float = 0.0


@dataclass
class RealtimeStream:
    """Поток realtime."""
    frames: list[RealtimeFrame] = field(default_factory=list)
    active: bool = False

    def push(self, frame: RealtimeFrame) -> None:
        self.frames.append(frame)
        if len(self.frames) > 100:
            self.frames = self.frames[-100:]


_STREAM: RealtimeStream | None = None


def get_stream() -> RealtimeStream:
    global _STREAM
    if _STREAM is None:
        _STREAM = RealtimeStream()
    return _STREAM


async def capture_once() -> RealtimeFrame:
    """Захватить один мультимодальный снимок."""
    import time
    f = RealtimeFrame(ts=time.time())
    # STT
    try:
        from aura.agents.listener import AgentListener
        lst = AgentListener()
        if hasattr(lst, "listen"):
            text = await asyncio.to_thread(lst.listen, 1)
            if text:
                f.audio_text = str(text)
    except Exception:
        pass
    # Vision: emotions
    try:
        from aura.agents.facial_emotion import AgentFacialEmotion
        from aura.core.protocol import AgentRequest
        agent = AgentFacialEmotion()
        resp = await agent.handle(AgentRequest(text="проверь моё лицо"))
        if "лиц" in resp.text.lower():
            import re
            m = re.search(r"(\d+)", resp.text)
            if m:
                f.video_faces = int(m.group(1))
    except Exception:
        pass
    return f


def summary() -> dict:
    s = get_stream()
    return {
        "frames": len(s.frames),
        "last_audio": s.frames[-1].audio_text if s.frames else "",
        "last_faces": s.frames[-1].video_faces if s.frames else 0,
    }


__all__ = ["RealtimeFrame", "RealtimeStream", "capture_once", "get_stream", "summary"]
