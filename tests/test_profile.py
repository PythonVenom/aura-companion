"""#12 UserProfile — тесты агрегации."""
from __future__ import annotations

import json

import pytest

from aura.core import profile as P


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    """Каждый тест — своя изолированная config-папка."""
    monkeypatch.setattr(P, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(P, "PROFILE_TXT", tmp_path / "profile")
    monkeypatch.setattr(P, "PROFILE_JSON", tmp_path / "profile.json")
    monkeypatch.setattr(P, "SETTINGS", tmp_path / "settings.json")
    monkeypatch.setattr(P, "SOS", tmp_path / "sos.json")
    monkeypatch.setattr(P, "FIN_ELDER", tmp_path / "fin_elder.json")
    monkeypatch.setattr(P, "SAFETY", tmp_path / "safety.json")
    yield


def test_load_empty_returns_defaults():
    p = P.UserProfile.load()
    assert p.name == "captain"
    assert p.persona == {}
    assert p.sos_contact == {}


def test_load_legacy_profile_txt():
    P.PROFILE_TXT.write_text("batya", encoding="utf-8")
    p = P.UserProfile.load()
    assert p.name == "batya"


def test_load_aggregates_settings():
    P.SETTINGS.write_text(json.dumps({"persona": {"name": "Аура"}}), encoding="utf-8")
    p = P.UserProfile.load()
    assert p.persona == {"name": "Аура"}


def test_load_aggregates_sos():
    P.SOS.write_text(json.dumps({"contact": "+7", "name": "сын"}), encoding="utf-8")
    p = P.UserProfile.load()
    assert p.sos_contact == {"contact": "+7", "name": "сын"}


def test_load_aggregates_fin_elder():
    P.FIN_ELDER.write_text(json.dumps({"pension_day": 8}), encoding="utf-8")
    p = P.UserProfile.load()
    assert p.fin_elder == {"pension_day": 8}


def test_load_aggregates_safety():
    P.SAFETY.write_text(json.dumps({"sos": {"enabled": True}}), encoding="utf-8")
    p = P.UserProfile.load()
    assert p.safety == {"sos": {"enabled": True}}


def test_load_priority_json_over_legacy():
    """Если profile.json есть — читаем его, а не legacy."""
    P.PROFILE_TXT.write_text("legacy", encoding="utf-8")
    P.PROFILE_JSON.write_text(
        json.dumps({"name": "new", "age": 78, "city": "Москва"}),
        encoding="utf-8",
    )
    p = P.UserProfile.load()
    assert p.name == "new"
    assert p.age == 78
    assert p.city == "Москва"


def test_save_creates_json():
    p = P.UserProfile(name="batya", age=78, city="Москва")
    p.save()
    assert P.PROFILE_JSON.exists()
    data = json.loads(P.PROFILE_JSON.read_text(encoding="utf-8"))
    assert data["name"] == "batya"
    assert data["age"] == 78


def test_save_load_roundtrip():
    p1 = P.UserProfile(
        name="batya", age=78, city="Москва",
        persona={"name": "Аура"},
        sos_contact={"contact": "+7"},
    )
    p1.save()
    p2 = P.UserProfile.load()
    assert p2.name == p1.name
    assert p2.age == p1.age
    assert p2.city == p1.city
    assert p2.persona == p1.persona
    assert p2.sos_contact == p1.sos_contact


def test_save_creates_dir(tmp_path, monkeypatch):
    nested = tmp_path / "deep" / "nested"
    monkeypatch.setattr(P, "CONFIG_DIR", nested)
    monkeypatch.setattr(P, "PROFILE_JSON", nested / "profile.json")
    p = P.UserProfile(name="test")
    p.save()
    assert (nested / "profile.json").exists()


def test_to_dict_serializes_signature():
    p = P.UserProfile(name="test")
    p.signature = b"\x01\x02\x03"
    d = p.to_dict()
    assert d["signature"] == "010203"


def test_to_dict_none_signature():
    p = P.UserProfile(name="test")
    d = p.to_dict()
    assert d["signature"] is None


def test_str_no_sos():
    p = P.UserProfile(name="test")
    assert "sos=❌" in str(p)


def test_str_with_sos():
    p = P.UserProfile(name="test", sos_contact={"contact": "+7"})
    assert "sos=✅" in str(p)


def test_load_broken_json_does_not_crash():
    P.SETTINGS.write_text("{broken", encoding="utf-8")
    p = P.UserProfile.load()
    assert p.persona == {}  # fallback


def test_load_broken_profile_json_falls_back():
    """Если profile.json битый — падаем на legacy."""
    P.PROFILE_TXT.write_text("captain", encoding="utf-8")
    P.PROFILE_JSON.write_text("{broken", encoding="utf-8")
    # profile.json существует → идём в первую ветку, но _read_json вернёт {}
    # name станет default "captain"
    p = P.UserProfile.load()
    assert p.name == "captain"
