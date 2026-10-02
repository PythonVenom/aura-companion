"""Тесты Accessibility (ADR-130)."""
from __future__ import annotations


def test_profiles_list():
    from aura.ui.accessibility import list_profiles
    ps = list_profiles()
    assert "default" in ps
    assert "elder" in ps
    assert "low_vision" in ps
    assert "screen_reader" in ps


def test_set_profile():
    from aura.ui.accessibility import set_profile, get_profile
    assert set_profile("elder")
    assert get_profile().name == "elder"
    assert set_profile("default")
    assert get_profile().name == "default"


def test_set_invalid_profile():
    from aura.ui.accessibility import set_profile
    assert not set_profile("nonsense")


def test_elder_max_words():
    from aura.ui.accessibility import set_profile, get_profile
    set_profile("elder")
    assert get_profile().max_words_response == 15
    set_profile("default")


def test_trim_response():
    from aura.ui.accessibility import trim_response
    long = " ".join(["a"] * 30)
    out = trim_response(long, max_words=5)
    assert out.count(" ") == 5  # 5 слов + "..." => 5 пробелов
    assert out.endswith("...")


def test_trim_short_unchanged():
    from aura.ui.accessibility import trim_response
    assert trim_response("короткий ответ", max_words=10) == "короткий ответ"


def test_contrast_white_black():
    from aura.ui.accessibility import contrast_ratio
    r = contrast_ratio((255, 255, 255), (0, 0, 0))
    assert r > 20  # white/black = 21:1


def test_wcag_aa_pass():
    from aura.ui.accessibility import passes_wcag_aa
    assert passes_wcag_aa((255, 255, 255), (0, 0, 0))       # 21:1
    assert passes_wcag_aa((255, 255, 255), (80, 80, 80))     # ~5:1


def test_wcag_aa_fail():
    from aura.ui.accessibility import passes_wcag_aa
    assert not passes_wcag_aa((200, 200, 200), (180, 180, 180))


def test_wcag_aaa():
    from aura.ui.accessibility import passes_wcag_aaa
    assert passes_wcag_aaa((255, 255, 255), (0, 0, 0))
    assert not passes_wcag_aaa((255, 255, 255), (120, 120, 120))
