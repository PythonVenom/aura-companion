"""Voice Profiles (ADR-040)."""
from aura import voice_profiles as vp


def test_profiles_count():
    assert len(vp.PROFILES) == 7


def test_get_default():
    p = vp.get_profile("default")
    assert p.name == "default"
    assert p.rate == 1.0


def test_get_medical():
    p = vp.get_profile("medical")
    assert p.style == "neutral"
    assert p.vocab == "medical"


def test_get_unknown_fallback():
    p = vp.get_profile("nonexistent")
    assert p.name == "default"


def test_list_profiles():
    lst = vp.list_profiles()
    assert len(lst) == 7
    names = [p.name for p in lst]
    assert "medical" in names
    assert "craft" in names


def test_apply_to_persona():
    persona = {"name": "Аура", "address": "ты"}
    result = vp.apply_to_persona("medical", persona)
    assert result["style"] == "neutral"
    assert result["rate"] == 1.1
    assert result["name"] == "Аура"  # сохранили


def test_apply_unknown():
    result = vp.apply_to_persona("xxx", {"name": "A"})
    assert result["style"] == "warm"  # default
