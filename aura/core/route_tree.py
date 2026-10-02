"""RouteTree — конкретная BT для Aura (ADR-094)."""
from __future__ import annotations
from aura.core.router_bt import Selector, Leaf


def _build_control_leaf():
    return Leaf(
        "control",
        match=lambda t, c: any(k in t.lower() for k in (
            "пауза", "продолжи", "замолчи", "стоп",
            "перезапусти", "kill", "убей", "panic",
        )),
        action=lambda t, c: {"route": "control", "text": t},
    )


def _build_open_leaf():
    return Leaf(
        "open",
        match=lambda t, c: any(k in t.lower() for k in (
            "открой", "запусти", "включи приложение", "open ",
        )),
        action=lambda t, c: {"route": "open", "text": t},
    )


def _build_ask_leaf():
    return Leaf(
        "ask",
        match=lambda t, c: True,  # fallback
        action=lambda t, c: {"route": "ask", "text": t},
    )


def build_route_tree() -> Selector:
    return Selector("aura_root", [
        _build_control_leaf(),
        _build_open_leaf(),
        _build_ask_leaf(),
    ])


__all__ = ["build_route_tree"]
