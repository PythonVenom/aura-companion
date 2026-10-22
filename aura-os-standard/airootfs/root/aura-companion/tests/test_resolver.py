"""Тесты Resolution Cascade."""
from __future__ import annotations
from aura.core.resolver import ResolutionCascade, ResolutionStep


def _step(name, ret):
    return ResolutionStep(name, resolve=lambda t, c: ret)


def test_first_level():
    c = ResolutionCascade([_step("app", "/usr/bin/code"), _step("web", "https://x")])
    r = c.resolve("code")
    assert r["level"] == "app"


def test_second_level():
    c = ResolutionCascade([_step("app", None), _step("web", "https://x")])
    r = c.resolve("code")
    assert r["level"] == "web"


def test_no_match():
    c = ResolutionCascade([_step("app", None), _step("web", None)])
    r = c.resolve("code")
    assert r["level"] == "none"


def test_exception_in_step():
    def boom(t, c):
        raise RuntimeError("boom")
    c = ResolutionCascade([
        ResolutionStep("bad", boom),
        _step("web", "https://x"),
    ])
    r = c.resolve("code")
    assert r["level"] == "web"


def test_empty_cascade():
    c = ResolutionCascade([])
    r = c.resolve("code")
    assert r["level"] == "none"
