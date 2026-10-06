"""Минимальный i18n для Aura (ADR-118)."""
from __future__ import annotations
from pathlib import Path
import os
import yaml

_LOCALES: dict[str, dict] = {}
_LANG = "ru"
_FALLBACK = "en"

def _load():
    d = Path(__file__).parent / "locales"
    for f in d.glob("*.yaml"):
        _LOCALES[f.stem] = yaml.safe_load(f.read_text(encoding="utf-8")) or {}

def available() -> list[str]:
    if not _LOCALES: _load()
    return sorted(_LOCALES.keys())

def set_lang(code: str) -> None:
    global _LANG
    if not _LOCALES: _load()
    _LANG = code if code in _LOCALES else _FALLBACK

def get_lang() -> str: return _LANG

def t(key: str, **kw) -> str:
    if not _LOCALES: _load()
    for lang in (_LANG, _FALLBACK, "ru"):
        v = _LOCALES.get(lang, {}).get(key)
        if v:
            try: return v.format(**kw)
            except Exception: return v
    return key

def detect_from_env() -> str:
    raw = os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
    code = raw.split(".")[0].split("_")[0].lower()
    return code if code in available() else _FALLBACK
