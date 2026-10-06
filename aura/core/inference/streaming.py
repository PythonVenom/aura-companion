"""Streaming LLM backend (ADR-127).

Наука:
- Kwon, W. et al. (2023). vLLM: PagedAttention. SOSP.
- Yu, G-I. et al. (2022). Orca: Continuous Batching.
- Zheng, L. et al. (2023). SGLang.

Реализация — Ollama /api/chat stream=true, токен-за-токеном.
Цель: TTFT < 500ms для голосового ответа.
"""
from __future__ import annotations

import json
import urllib.request
from collections.abc import Iterator

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct-q4_K_M"
TIMEOUT = 60


def stream_chat(messages: list[dict],
                model: str = MODEL,
                temperature: float = 0.3,
                num_predict: int = 300) -> Iterator[str]:
    """Стрим ответа токен-за-токеном. Yield chunks (str)."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL, data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            for raw_line in r:
                if not raw_line.strip():
                    continue
                try:
                    chunk = json.loads(raw_line.decode("utf-8"))
                except Exception:
                    continue
                msg = chunk.get("message", {})
                piece = msg.get("content", "")
                if piece:
                    yield piece
                if chunk.get("done"):
                    break
    except Exception as e:
        yield f"[stream error: {e}]"


def generate(messages: list[dict],
             model: str = MODEL,
             temperature: float = 0.3,
             num_predict: int = 300) -> str:
    """Non-streaming — собрать ответ полностью."""
    return "".join(stream_chat(messages, model, temperature, num_predict))


def stream_measure(messages: list[dict]) -> dict:
    """Замерить TTFT и TPS. Для метрик (ADR-127)."""
    import time
    t0 = time.time()
    ttft: float | None = None
    chunks = 0
    text = ""
    for chunk in stream_chat(messages):
        if ttft is None:
            ttft = time.time() - t0
        chunks += 1
        text += chunk
    total = time.time() - t0
    tps = chunks / total if total > 0 else 0
    return {"ttft_ms": int((ttft or 0) * 1000),
            "total_ms": int(total * 1000),
            "chunks": chunks, "tps": round(tps, 1), "text": text}
