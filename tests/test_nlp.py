"""NLP fuzzy_match + adaptive."""
from aura.nlp import fuzzy_match, _levenshtein, _adaptive_dist


def test_lev_eq():
    assert _levenshtein("abc", "abc") == 0


def test_lev_sub():
    assert _levenshtein("выключи", "выключит") == 1


def test_lev_2sub():
    assert _levenshtein("перезагрузи", "перезагружу") == 2


def test_adaptive_short():
    assert _adaptive_dist("сон") == 0
    assert _adaptive_dist("lock") == 0


def test_adaptive_mid():
    assert _adaptive_dist("выключи") == 1
    assert _adaptive_dist("spящий") == 1


def test_adaptive_long():
    assert _adaptive_dist("перезагрузи") == 2
    assert _adaptive_dist("заблокируй") == 2


def test_exact_substring():
    assert fuzzy_match("выключи пк", ["выключи"]) is True


def test_1edit_mid_word():
    assert fuzzy_match("выключит пк", ["выключи"]) is True


def test_2edit_long_word():
    # "перезагружу" vs "перезагрузи" — 2 правки, len 11 → adaptive 2
    assert fuzzy_match("перезагружу комп", ["перезагрузи"]) is True


def test_short_word_strict():
    # "сон" (3) → adaptive 0, "сок" не должен матчиться
    assert fuzzy_match("выпил сок", ["сон"]) is False


def test_unrelated_far():
    assert fuzzy_match("привет мир", ["выключи"]) is False


def test_empty():
    assert fuzzy_match("", ["выключи"]) is False
    assert fuzzy_match("привет", []) is False
