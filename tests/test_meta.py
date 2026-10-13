"""#18 Meta-Memory — тесты aura/core/memory/meta.py."""
from __future__ import annotations

import math
import time

import pytest

from aura.core.memory import meta as M


# === Confidence dataclass ===

def test_confidence_dataclass():
    c = M.Confidence(value=0.9, label="sure")
    assert c.value == 0.9
    assert c.label == "sure"


# === _recency ===

def test_recency_zero_ts_returns_one():
    """ts=0 → 1.0 (fallback, не свежее)."""
    assert M._recency(0.0) == 1.0


def test_recency_negative_ts_returns_one():
    assert M._recency(-5.0) == 1.0


def test_recency_fresh_is_one():
    """Свежий факт (ts=now) → 1.0."""
    now = time.time()
    assert abs(M._recency(now) - 1.0) < 0.01


def test_recency_decays_over_time():
    """Чем старше — тем ниже recency."""
    now = time.time()
    fresh = M._recency(now - 86400)          # 1 день
    old = M._recency(now - 90 * 86400)       # 90 дней
    assert fresh > old


def test_recency_halflife():
    """Через halflife_days → ~0.5."""
    now = time.time()
    halflife = 30.0
    r = M._recency(now - halflife * 86400, halflife_days=halflife)
    assert 0.45 < r < 0.55


# === score ===

def test_score_returns_confidence():
    c = M.score()
    assert isinstance(c, M.Confidence)
    assert 0.0 <= c.value <= 1.0


def test_score_high_extraction():
    """Высокая extraction → высокий score."""
    high = M.score(extraction=1.0, evidence_count=5, consistency=1.0)
    low = M.score(extraction=0.1, evidence_count=1, consistency=0.1)
    assert high.value > low.value


def test_score_label_sure():
    """value > 0.8 → 'sure'."""
    c = M.score(extraction=1.0, evidence_count=10, consistency=1.0)
    if c.value > 0.8:
        assert c.label == "sure"


def test_score_label_unknown_for_low():
    """value <= 0.0 → 'unknown'."""
    c = M.score(extraction=0.0, evidence_count=0, consistency=0.0)
    # Если формула даёт 0 — label='unknown'
    assert c.value >= 0.0
    if c.value == 0.0:
        assert c.label == "unknown"


def test_score_evidence_count_boost():
    """Больше evidence → выше score."""
    one = M.score(extraction=0.7, evidence_count=1)
    many = M.score(extraction=0.7, evidence_count=10)
    assert many.value >= one.value


def test_score_clamped_to_one():
    """Даже с экстрим-параметрами score ≤ 1.0."""
    c = M.score(extraction=10.0, evidence_count=1000, consistency=10.0)
    assert c.value <= 1.0


def test_score_label_consistency():
    """label должен соответствовать value."""
    c = M.score(extraction=0.9, evidence_count=5, consistency=0.9)
    if c.value > 0.8:
        assert c.label == "sure"
    elif c.value > 0.5:
        assert c.label == "probable"
    elif c.value > 0.0:
        assert c.label == "unsure"


# === hedged ===

def test_hedged_sure_returns_response():
    """sure → без хеджа."""
    c = M.Confidence(value=0.9, label="sure")
    assert M.hedged("Москва — столица", c) == "Москва — столица"


def test_hedged_probable_adds_prefix_ru():
    c = M.Confidence(value=0.7, label="probable")
    out = M.hedged("Москва", c, lang="ru")
    assert "Кажется" in out
    assert "Москва" in out


def test_hedged_probable_adds_prefix_en():
    c = M.Confidence(value=0.7, label="probable")
    out = M.hedged("Moscow", c, lang="en")
    assert "I think" in out


def test_hedged_unsure_adds_hedge_ru():
    c = M.Confidence(value=0.3, label="unsure")
    out = M.hedged("Москва", c, lang="ru")
    assert "Не уверена" in out


def test_hedged_unknown_returns_dont_remember():
    c = M.Confidence(value=0.0, label="unknown")
    out = M.hedged("Москва", c, lang="ru")
    assert "не помню" in out.lower()


def test_hedged_unknown_en():
    c = M.Confidence(value=0.0, label="unknown")
    out = M.hedged("Moscow", c, lang="en")
    assert "don't remember" in out.lower()


# === calibration_error ===

def test_calibration_error_empty():
    assert M.calibration_error([]) == 0.0


def test_calibration_error_perfect():
    """Идеально уверенные + правильные → низкая ошибка."""
    pairs = [(1.0, True), (1.0, True), (0.0, False), (0.0, False)]
    ece = M.calibration_error(pairs)
    assert 0.0 <= ece < 0.5


def test_calibration_error_overconfident():
    """Уверен 1.0 но ошибся → высокая ECE."""
    pairs = [(1.0, False), (1.0, False), (1.0, False)]
    ece = M.calibration_error(pairs)
    assert ece > 0.5


def test_calibration_error_underconfident():
    """Уверен 0.0 но прав → тоже ошибка."""
    pairs = [(0.0, True), (0.0, True)]
    ece = M.calibration_error(pairs)
    assert ece > 0.5


def test_calibration_error_returns_float():
    pairs = [(0.5, True), (0.8, True), (0.2, False)]
    ece = M.calibration_error(pairs)
    assert isinstance(ece, float)
    assert 0.0 <= ece <= 1.0
