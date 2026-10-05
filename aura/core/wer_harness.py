"""T083 — WER harness (Word Error Rate для ASR).

Наука:
- Levenshtein 1966 — расстояние редактирования
- Jurafsky & Martin, «Speech and Language Processing» — WER
- NIST SCTK (sclite) 2000 — эталон оценки ASR
- Kaldi docs (Povey 2011) — как WER считается в ASR
- Ziel: WER ≤ 5% для русского elder-care домена (T083)

WER = (S + D + I) / N
  S — substitutions (замены)
  D — deletions (пропуски)
  I — insertions (вставки)
  N — число слов в reference

Поддерживает нормализацию (lowercase + пунктуация).
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path
from typing import Iterable

RESULTS_DIR = Path.home() / ".local/share/aura/wer"
RESULTS_FILE = RESULTS_DIR / "results.jsonl"

TARGET_WER = 0.05  # 5%

# Наука: Kaldi docs — нормализация обязательна перед WER
PUNCT_RE = re.compile(r"[^\w\s]|_", re.UNICODE)
SPACE_RE = re.compile(r"\s+")


def _ensure() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def normalize(text: str) -> str:
    """Lowercase + удалить пунктуацию + collapse spaces."""
    if not text:
        return ""
    t = text.lower()
    t = PUNCT_RE.sub(" ", t)
    t = SPACE_RE.sub(" ", t).strip()
    return t


def _levenshtein_counts(ref: list[str], hyp: list[str]) -> tuple[int, int, int]:
    """Levenshtein alignment → (S, D, I).

    Классический DP (Levenshtein 1966), с backtrack по матрице.
    """
    n, m = len(ref), len(hyp)
    # dp[i][j] = (S, D, I) для ref[:i], hyp[:j]
    dp: list[list[tuple[int, int, int]]] = [
        [(0, 0, 0)] * (m + 1) for _ in range(n + 1)
    ]
    # базовые случаи
    for i in range(1, n + 1):
        s, d, ins = dp[i - 1][0]
        dp[i][0] = (s, d + 1, ins)  # deletion
    for j in range(1, m + 1):
        s, d, ins = dp[0][j - 1]
        dp[0][j] = (s, d, ins + 1)  # insertion

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
                continue
            # substitution
            s, d, ins = dp[i - 1][j - 1]
            cand_sub = (s + 1, d, ins)
            # deletion
            s, d, ins = dp[i - 1][j]
            cand_del = (s, d + 1, ins)
            # insertion
            s, d, ins = dp[i][j - 1]
            cand_ins = (s, d, ins + 1)
            # выбираем по сумме (S+D+I)
            dp[i][j] = min(
                (cand_sub, cand_del, cand_ins),
                key=lambda x: x[0] + x[1] + x[2],
            )
    return dp[n][m]


def wer(reference: str, hypothesis: str) -> dict:
    """WER одной пары (reference, hypothesis)."""
    ref = normalize(reference).split()
    hyp = normalize(hypothesis).split()
    if not ref:
        return {"wer": 0.0 if not hyp else 1.0, "S": 0, "D": 0, "I": len(hyp),
                "N": 0, "ref": "", "hyp": ""}
    s, d, i = _levenshtein_counts(ref, hyp)
    value = (s + d + i) / len(ref)
    return {
        "wer": round(value, 4),
        "S": s, "D": d, "I": i,
        "N": len(ref),
        "ref": " ".join(ref),
        "hyp": " ".join(hyp),
        "pass": value <= TARGET_WER,
    }


def corpus_wer(pairs: Iterable[tuple[str, str]]) -> dict:
    """WER по корпусу (суммируем S/D/I, делим на общий N)."""
    total_s = total_d = total_i = total_n = 0
    items = []
    for ref, hyp in pairs:
        r = wer(ref, hyp)
        items.append(r)
        total_s += r["S"]
        total_d += r["D"]
        total_i += r["I"]
        total_n += r["N"]
    value = (total_s + total_d + total_i) / total_n if total_n else 1.0
    return {
        "wer": round(value, 4),
        "S": total_s, "D": total_d, "I": total_i, "N": total_n,
        "samples": len(items),
        "target": TARGET_WER,
        "pass": value <= TARGET_WER,
    }


def record(operation: str, ref: str, hyp: str) -> dict:
    """Записать одну пару в RESULTS_FILE."""
    _ensure()
    result = wer(ref, hyp)
    entry = {
        "ts": time.time(),
        "operation": operation,
        **result,
    }
    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def load_history() -> list[dict]:
    if not RESULTS_FILE.exists():
        return []
    out = []
    for line in RESULTS_FILE.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def wer_report() -> dict:
    """Публичный API: сводка по всей истории."""
    history = load_history()
    if not history:
        return {"samples": 0, "wer": None, "target": TARGET_WER, "pass": None}
    total_s = sum(h.get("S", 0) for h in history)
    total_d = sum(h.get("D", 0) for h in history)
    total_i = sum(h.get("I", 0) for h in history)
    total_n = sum(h.get("N", 0) for h in history)
    value = (total_s + total_d + total_i) / total_n if total_n else 1.0
    return {
        "samples": len(history),
        "wer": round(value, 4),
        "S": total_s, "D": total_d, "I": total_i, "N": total_n,
        "target": TARGET_WER,
        "pass": value <= TARGET_WER,
    }


def reset() -> None:
    if RESULTS_FILE.exists():
        RESULTS_FILE.unlink()


__all__ = [
    "normalize", "wer", "corpus_wer", "record",
    "load_history", "wer_report", "reset",
    "TARGET_WER",
]
