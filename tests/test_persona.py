"""Тесты persona.py — сборка системного промпта (ADR-046)."""
import pytest
from aura import persona


def test_defaults_empty_persona():
    p = persona.build_system_prompt({})
    assert "Аура" in p
    assert "друг" in p
    assert "тёпл" in p.lower()


def test_defaults_none():
    p = persona.build_system_prompt(None)
    assert "Аура" in p


def test_name_in_prompt():
    p = persona.build_system_prompt({"name": "Катя"})
    assert "Катя" in p
    assert "Аура" not in p


def test_user_name_and_gender():
    p = persona.build_system_prompt({"user_name": "Иван", "user_gender": "м"})
    assert "Иван" in p
    assert "мужчина" in p


def test_gender_he():
    p = persona.build_system_prompt({"gender": "он"})
    assert "мужского" in p


def test_gender_neutral():
    p = persona.build_system_prompt({"gender": "нейтр"})
    assert "вне рода" in p


def test_role_drug():
    p = persona.build_system_prompt({"role": "друг"})
    assert "друг" in p.lower()


def test_role_nastavnik():
    p = persona.build_system_prompt({"role": "наставник"})
    assert "наставник" in p.lower()


def test_style_sarcastic():
    p = persona.build_system_prompt({"style": "саркастичная"})
    assert "сарказ" in p.lower()


def test_humor_true():
    p = persona.build_system_prompt({"humor": True})
    assert "Шути" in p


def test_humor_false():
    p = persona.build_system_prompt({"humor": False})
    assert "Без шуток" in p


def test_address_vy():
    p = persona.build_system_prompt({"address": "вы"})
    assert "«вы»" in p


def test_tone_brief():
    p = persona.build_system_prompt({"tone": "кратко"})
    assert "кратко" in p


def test_describe_basic():
    d = persona.describe({"name": "Аура", "role": "друг", "user_name": "Макс"})
    assert "Аура" in d
    assert "Макс" in d


def test_describe_defaults():
    d = persona.describe({})
    assert "Аура" in d


def test_empty_string_uses_default():
    p = persona.build_system_prompt({"name": ""})
    assert "Аура" in p
