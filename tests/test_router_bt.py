"""Тесты Behavior Tree роутера."""
from __future__ import annotations
from aura.core.router_bt import Selector, Sequence, Leaf


def _leaf(name, match_sub, result):
    return Leaf(
        name,
        match=lambda t, c: match_sub in t.lower(),
        action=lambda t, c: result,
    )


def test_selector_first_match():
    bt = Selector("root", [
        _leaf("control", "пауза", "PAUSE"),
        _leaf("open", "открой", "OPEN"),
    ])
    assert bt.handle("пауза", {}) == "PAUSE"


def test_selector_second_match():
    bt = Selector("root", [
        _leaf("control", "пауза", "PAUSE"),
        _leaf("open", "открой", "OPEN"),
    ])
    assert bt.handle("открой вк", {}) == "OPEN"


def test_selector_no_match():
    bt = Selector("root", [_leaf("control", "пауза", "PAUSE")])
    assert bt.handle("бла бла", {}) is None


def test_sequence_all_match():
    bt = Sequence("root", [
        _leaf("a", "тест", "A"),
        _leaf("b", "тест", "B"),
    ])
    assert bt.handle("тест тест", {}) == "B"


def test_sequence_partial():
    bt = Sequence("root", [
        _leaf("a", "тест", "A"),
        _leaf("b", "нет", "B"),
    ])
    assert bt.handle("тест", {}) is None


def test_nested():
    inner = Selector("inner", [
        _leaf("app", "vscode", "APP"),
        _leaf("web", "браузер", "WEB"),
    ])
    outer = Selector("outer", [
        _leaf("ctrl", "пауза", "PAUSE"),
        inner,
    ])
    assert outer.handle("открой браузер", {}) == "WEB"
    assert outer.handle("пауза", {}) == "PAUSE"
