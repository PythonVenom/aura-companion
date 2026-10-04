"""Accessibility — WCAG 2.2 AA + Elder care (ADR-130).

Наука:
- W3C (2023). WCAG 2.2.
- Lazar, J. et al. (2017). Ensuring Digital Accessibility.

Профили: default | elder | low_vision | screen_reader.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class A11yProfile:
    name: str
    font_pt: int = 14
    contrast_min: float = 4.5         # WCAG 2.2 AA
    target_size_px: int = 24
    speech_rate: float = 1.0          # 1.0 = обычная, 0.85 = медленнее
    max_words_response: int = 0        # 0 = без лимита
    captions: bool = True
    timeout_seconds: int = 0           # 0 = без таймаута


PROFILES = {
    "default": A11yProfile(
        name="default", font_pt=14, contrast_min=4.5,
        target_size_px=24, speech_rate=1.0, max_words_response=0,
    ),
    "elder": A11yProfile(
        name="elder", font_pt=20, contrast_min=7.0,
        target_size_px=48, speech_rate=0.85,
        max_words_response=15, timeout_seconds=0,
    ),
    "low_vision": A11yProfile(
        name="low_vision", font_pt=24, contrast_min=7.0,
        target_size_px=48, speech_rate=0.95,
        max_words_response=20, captions=True,
    ),
    "screen_reader": A11yProfile(
        name="screen_reader", font_pt=18, contrast_min=4.5,
        target_size_px=44, speech_rate=0.9,
        max_words_response=25, captions=True,
    ),
}


_current_name = "default"


def set_profile(name: str) -> bool:
    global _current_name
    if name in PROFILES:
        _current_name = name
        return True
    return False


def get_profile() -> A11yProfile:
    return PROFILES[_current_name]


def current_name() -> str:
    return _current_name


def list_profiles() -> list[str]:
    return sorted(PROFILES.keys())


def contrast_ratio(rgb1: tuple, rgb2: tuple) -> float:
    """WCAG формула контраста. >4.5 = AA, >7.0 = AAA."""
    def lum(c):
        def ch(v):
            v = v / 255.0
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        r, g, b = c
        return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)
    l1, l2 = lum(rgb1), lum(rgb2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def passes_wcag_aa(rgb1: tuple, rgb2: tuple, large_text: bool = False) -> bool:
    """AA: 4.5:1 для обычного текста, 3:1 для крупного (≥18pt)."""
    ratio = contrast_ratio(rgb1, rgb2)
    return ratio >= (3.0 if large_text else 4.5)


def passes_wcag_aaa(rgb1: tuple, rgb2: tuple, large_text: bool = False) -> bool:
    """AAA: 7:1 обычный, 4.5:1 крупный."""
    ratio = contrast_ratio(rgb1, rgb2)
    return ratio >= (4.5 if large_text else 7.0)


def trim_response(text: str, max_words: Optional[int] = None) -> str:
    """Обрезать ответ по лимиту профиля (elder: 15 слов)."""
    limit = max_words if max_words is not None else get_profile().max_words_response
    if not limit:
        return text
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit]) + "..."
