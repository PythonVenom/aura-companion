"""Тесты словаря и персоны."""


from aura.lore import LINES, PHRASES, speak_line, translate
from aura.lore.terminology import TERMS


# ── translate ──────────────────────────────────────────────
def test_translate_ruff():
    assert "энергоблок" in translate("Ruff нашёл 3 ошибки")

def test_translate_pytest():
    assert "диагностика корпуса" in translate("pytest 1570 passed")

def test_translate_branch():
    assert "сектор" in translate("branch master")

def test_translate_commit():
    assert "координаты" in translate("commit b9b8978")

def test_translate_bug():
    assert "пробоина" in translate("bug in speaker.py")

def test_translate_empty():
    assert translate("") == ""
    assert translate(None) is None  # type: ignore[arg-type]

def test_translate_multiple():
    out = translate("ruff 0, pytest 1570 passed, branch master")
    assert "энергоблок" in out
    assert "узлы" in out or "диагностика корпуса" in out
    assert "сектор" in out
    assert "Ruff" not in out
    assert "pytest" not in out
    assert "branch" not in out


# ── speak_line ─────────────────────────────────────────────
def test_speak_line_morning():
    line = speak_line("morning", day=4, sector="STABILIZE", xp=420)
    assert "День 4" in line
    assert "STABILIZE" in line

def test_speak_line_fix_success():
    line = speak_line("fix_success", hull=1570)
    assert "Залп принят" in line
    assert "1570" in line

def test_speak_line_unknown_event():
    assert speak_line("nonsense_event") == LINES["unknown"]

def test_speak_line_missing_param_does_not_crash():
    line = speak_line("morning", day=1)  # нет sector, xp
    assert "не хватает" in line

def test_phrases_present():
    assert "yes" in PHRASES
    assert "ready" in PHRASES

def test_terms_are_regex_safe():
    import re
    for pattern in TERMS:
        re.compile(pattern)  # не должно бросить
