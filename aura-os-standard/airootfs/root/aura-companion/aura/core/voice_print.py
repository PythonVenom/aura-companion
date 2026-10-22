"""Voice Print — голосовая подпись капитана (F-074 расширение).

Наука: Speaker Verification (Reynolds 2000, i-vector).
Fallback: energy + pitch (без ML).
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

PRINT_FILE = Path.home() / ".cache" / "aura" / "voice_print.json"


@dataclass
class VoicePrint:
    """Слепок голоса: средний RMS, zero-crossings, длина."""
    samples: int = 0
    rms_avg: float = 0.0
    zcr_avg: float = 0.0
    verified_count: int = 0
    rejected_count: int = 0
    registered_at: float = 0.0
    history: list[dict] = field(default_factory=list)


_PRINT: VoicePrint | None = None


def _load() -> VoicePrint:
    if PRINT_FILE.exists():
        try:
            data = json.loads(PRINT_FILE.read_text(encoding="utf-8"))
            return VoicePrint(**{k: v for k, v in data.items()
                                 if k in VoicePrint.__dataclass_fields__})
        except Exception:
            pass
    return VoicePrint()


def _save(p: VoicePrint) -> None:
    try:
        PRINT_FILE.parent.mkdir(parents=True, exist_ok=True)
        PRINT_FILE.write_text(json.dumps(asdict(p), ensure_ascii=False, indent=2))
    except Exception:
        pass


def get_print() -> VoicePrint:
    global _PRINT
    if _PRINT is None:
        _PRINT = _load()
    return _PRINT


def _rms_and_zcr(audio_bytes: bytes) -> tuple[float, float]:
    """Считать RMS и ZCR из int16 PCM."""
    try:
        import numpy as np
        a = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        if len(a) == 0:
            return 0.0, 0.0
        rms = float(np.sqrt(np.mean(a * a)))
        zcr = float(np.mean(np.abs(np.diff(np.sign(a))) > 0))
        return rms, zcr
    except Exception:
        return 0.0, 0.0


def register(audio_bytes: bytes) -> VoicePrint:
    """Зарегистрировать голос."""
    p = get_print()
    rms, zcr = _rms_and_zcr(audio_bytes)
    n = p.samples + 1
    p.rms_avg = ((p.rms_avg * p.samples) + rms) / n
    p.zcr_avg = ((p.zcr_avg * p.samples) + zcr) / n
    p.samples = n
    p.registered_at = time.time()
    _save(p)
    return p


def verify(audio_bytes: bytes, tolerance: float = 0.3) -> bool:
    """Проверить голос. Возврат: True если совпадает."""
    p = get_print()
    if p.samples == 0:
        return False
    rms, zcr = _rms_and_zcr(audio_bytes)
    rms_ok = abs(rms - p.rms_avg) / max(p.rms_avg, 1.0) < tolerance
    zcr_ok = abs(zcr - p.zcr_avg) / max(p.zcr_avg, 0.01) < tolerance
    ok = rms_ok and zcr_ok
    if ok:
        p.verified_count += 1
    else:
        p.rejected_count += 1
    _save(p)
    return ok


def stats() -> dict:
    p = get_print()
    return {
        "samples": p.samples,
        "rms_avg": round(p.rms_avg, 1),
        "zcr_avg": round(p.zcr_avg, 4),
        "verified": p.verified_count,
        "rejected": p.rejected_count,
        "registered": p.samples > 0,
    }


__all__ = ["VoicePrint", "get_print", "register", "stats", "verify"]
