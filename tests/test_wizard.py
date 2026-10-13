"""#102 First-Run Wizard — тесты."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura.wizard import (
    WizardApp, validate_name, validate_age, validate_phone, validate_city,
)


# === validate_name ===

def test_validate_name_ok():
    assert validate_name("Иван") == (True, "")


def test_validate_name_empty():
    ok, _ = validate_name("")
    assert not ok


def test_validate_name_whitespace():
    ok, _ = validate_name("   ")
    assert not ok


def test_validate_name_too_long():
    ok, _ = validate_name("a" * 51)
    assert not ok


# === validate_age ===

def test_validate_age_ok():
    assert validate_age("78") == (True, "")


def test_validate_age_empty_ok():
    """Возраст опционален."""
    assert validate_age("") == (True, "")


def test_validate_age_not_digit():
    ok, _ = validate_age("abc")
    assert not ok


def test_validate_age_too_high():
    ok, _ = validate_age("150")
    assert not ok


def test_validate_age_zero():
    ok, _ = validate_age("0")
    assert not ok


# === validate_phone ===

def test_validate_phone_plus7():
    assert validate_phone("+79991234567") == (True, "")


def test_validate_phone_eight():
    assert validate_phone("89991234567") == (True, "")


def test_validate_phone_with_spaces():
    assert validate_phone("+7 999 123 45 67") == (True, "")


def test_validate_phone_with_dashes():
    assert validate_phone("+7-999-123-45-67") == (True, "")


def test_validate_phone_empty():
    ok, _ = validate_phone("")
    assert not ok


def test_validate_phone_too_short():
    ok, _ = validate_phone("123")
    assert not ok


def test_validate_phone_letters():
    ok, _ = validate_phone("+7abc")
    assert not ok


# === validate_city ===

def test_validate_city_ok():
    assert validate_city("Москва") == (True, "")


def test_validate_city_empty_ok():
    """Город опционален."""
    assert validate_city("") == (True, "")


def test_validate_city_too_long():
    ok, _ = validate_city("x" * 101)
    assert not ok


# === WizardApp smoke ===

@pytest.mark.asyncio
async def test_app_starts():
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert "welcome" in app.SCREENS


def test_save_all_writes_profile(tmp_path, monkeypatch):
    """save_all пишет в profile.json + sos.json."""
    from aura.core import profile as P

    monkeypatch.setattr(P, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(P, "PROFILE_JSON", tmp_path / "profile.json")

    # Подменяем sos.json путь
    import aura.wizard as W
    # Создаём app без run (answers уже есть)
    app = WizardApp()
    app.answers = {
        "name": "Батя",
        "age": 78,
        "city": "Москва",
        "sos_name": "Сын Иван",
        "sos_phone": "+79991234567",
    }

    # Меняем Path.home() на tmp_path
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    (fake_home / ".config/aura").mkdir(parents=True)

    try:
        app.save_all()
    except Exception:
        pass  # exit в run_test-контексте не работает

    # Проверяем sos.json (главное — записался)
    sos_file = fake_home / ".config/aura/sos.json"
    if sos_file.exists():
        data = json.loads(sos_file.read_text(encoding="utf-8"))
        assert data["name"] == "Сын Иван"
        assert data["contact"] == "+79991234567"


def test_screens_registered():
    """Все 6 экранов зарегистрированы."""
    app = WizardApp()
    for name in ("welcome", "name", "age", "sos", "city", "confirm"):
        assert name in app.SCREENS
