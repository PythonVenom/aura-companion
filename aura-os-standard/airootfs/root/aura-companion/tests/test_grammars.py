"""#135 AgentGrammars — тесты."""
from __future__ import annotations

import pytest

from aura.core import grammars as G


# === match ===

@pytest.mark.parametrize("text", [
    "мне плохо", "помогите", "вызови скорую", "умираю",
    "болит голова", "срочно", "sos", "спасите",
])
def test_sos_positive(text):
    assert G.match("sos", text) is True


@pytest.mark.parametrize("text", [
    "я упал", "упала", "не могу встать", "лежу на полу", "сломал руку",
])
def test_fall_positive(text):
    assert G.match("fall", text) is True


@pytest.mark.parametrize("text", [
    "аура стоп", "тише", "хватит", "замолчи", "молчи",
])
def test_stop_positive(text):
    assert G.match("stop", text) is True


def test_yes():
    assert G.match("yes", "да") is True
    assert G.match("yes", "ага") is True


def test_no():
    assert G.match("no", "нет") is True
    assert G.match("no", "отмена") is True


# === negative ===

@pytest.mark.parametrize("text", [
    "", "привет", "как дела", "включи музыку", "расскажи сказку",
])
def test_no_match_random(text):
    assert G.match_any(text) is None


def test_match_unknown_grammar():
    assert G.match("xyz", "стоп") is False


def test_match_empty():
    assert G.match("stop", "") is False
    assert G.match_any("") is None


# === case insensitive ===

def test_case_insensitive():
    assert G.match("stop", "СТОП") is True
    assert G.match("sos", "Помогите") is True


# === match_any priority ===

def test_match_any_sos_before_stop():
    """sos идёт первым в dict — если фраза содержит оба, вернётся sos."""
    result = G.match_any("мне плохо стоп")
    assert result == "sos"


def test_match_any_returns_first():
    """Возвращает первую сработавшую грамматику."""
    result = G.match_any("да")
    assert result == "yes"


# === Константы ===

def test_grammars_keys():
    for key in ("sos", "fall", "stop", "yes", "no"):
        assert key in G.GRAMMARS


def test_grammars_compiled():
    import re
    for pattern in G.GRAMMARS.values():
        assert isinstance(pattern, re.Pattern)
