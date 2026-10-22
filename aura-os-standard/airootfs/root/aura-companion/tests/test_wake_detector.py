"""Тесты wake_detector (2026-10-13).

Wake-word через fuzzy (Levenshtein 1965).
F-021d: «Аура» → «алло», «аула», «алла».
"""
from __future__ import annotations

import pytest

from aura.wake_detector import (
    CANONICAL,
    KNOWN_VARIANTS,
    WHITELIST_NO_WAKE,
    is_wake_word,
    levenshtein,
    strip_wake_word,
)


# ============================================================
# Levenshtein
# ============================================================
def test_levenshtein_identical():
    assert levenshtein("аура", "аура") == 0


def test_levenshtein_empty():
    assert levenshtein("", "аура") == 4
    assert levenshtein("аура", "") == 4
    assert levenshtein("", "") == 0


def test_levenshtein_one_letter():
    assert levenshtein("аура", "аула") == 1
    assert levenshtein("аура", "ура") == 1


def test_levenshtein_two():
    assert levenshtein("аура", "алла") == 2


def test_levenshtein_three():
    assert levenshtein("аура", "алло") == 3


# ============================================================
# is_wake_word — positive
# ============================================================
@pytest.mark.parametrize("text", [
    "Аура",
    "Аура, привет",
    "аура",
    "ауру",
    "ауры",
    "алло",
    "алла",
    "аула",
    "ауло",
    "лаура",
    "aura",
])
def test_is_wake_word_positive(text):
    assert is_wake_word(text), f"Не поймал: {text!r}"


# ============================================================
# is_wake_word — negative (ложные срабатывания)
# ============================================================
@pytest.mark.parametrize("text", [
    "ураган",
    "арахис",
    "пауза",
    "привет",
    "включи музыку",
    "ау",
    "ура",
    "как дела",
])
def test_is_wake_word_negative(text):
    assert not is_wake_word(text), f"Ложное срабатывание: {text!r}"


# ============================================================
# Elder-care whitelist
# ============================================================
@pytest.mark.parametrize("text", [
    "который час",
    "мне плохо",
    "вызови скорую",
    "sos",
    "тревога",
    "какая погода",
    "пора пить",
])
def test_is_wake_word_elder_whitelist(text):
    assert is_wake_word(text), f"Whitelist не сработал: {text!r}"


# ============================================================
# strip_wake_word
# ============================================================
def test_strip_wake_word_beginning():
    assert strip_wake_word("Аура привет") == "привет"


def test_strip_wake_word_end():
    assert strip_wake_word("привет аура") == "привет"


def test_strip_wake_word_middle():
    assert strip_wake_word("Аура какая погода") == "какая погода"


def test_strip_wake_word_empty():
    assert strip_wake_word("") == ""


def test_strip_wake_word_only():
    assert strip_wake_word("Аура") == ""


def test_strip_wake_word_variant():
    assert strip_wake_word("алло привет") == "привет"


# ============================================================
# Константы
# ============================================================
def test_constants_exist():
    assert CANONICAL
    assert KNOWN_VARIANTS
    assert WHITELIST_NO_WAKE
    assert "аура" in CANONICAL
    assert "алло" in KNOWN_VARIANTS
    assert "мне плохо" in WHITELIST_NO_WAKE
