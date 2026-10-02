"""RouteTree — конкретная BT для Aura (ADR-094, ADR-107, ADR-108)."""
from __future__ import annotations
import re
from aura.core.router_bt import Selector, Leaf


def _has(text: str, *keys: str) -> bool:
    t = text.lower()
    return any(k in t for k in keys)


def _strip(text: str, *keys: str) -> str:
    t = text
    for k in keys:
        t = re.sub(k, "", t, flags=re.IGNORECASE)
    return t.strip(" ,.!?")


def _build_control_leaf():
    def action(t, c):
        if _has(t, "продолжи", "resume", "дальше играй"):
            return {"route": "control", "action": "resume", "args": {}}
        return {"route": "control", "action": "pause", "args": {}}
    return Leaf(
        "control",
        match=lambda t, c: _has(t, "пауза", "продолжи", "замолчи", "стоп",
                                "перезапусти", "kill", "убей", "panic"),
        action=action,
    )


def _build_power_leaf():
    return Leaf(
        "power",
        match=lambda t, c: _has(t, "заблокируй", "lock screen", "залочь"),
        action=lambda t, c: {"route": "power", "action": "lock", "args": {}},
    )


def _build_music_leaf():
    def action(t, c):
        if _has(t, "следующ", "next", "дальше трек"):
            return {"route": "music", "action": "next", "args": {}}
        if _has(t, "предыдущ", "prev", "назад трек"):
            return {"route": "music", "action": "prev", "args": {}}
        if _has(t, "пауза", "pause", "останови музыку"):
            return {"route": "music", "action": "pause", "args": {}}
        q = _strip(t, r"\bвключи\b", r"\bпоставь\b", r"\bиграй\b",
                   r"\bplay\b", r"\bмузыку\b", r"\bтрек\b", r"\bпесню\b")
        return {"route": "music", "action": "play", "args": {"query": q}}
    return Leaf(
        "music",
        match=lambda t, c: _has(t, "включи", "поставь", "играй",
                                "следующ", "предыдущ", "pause", "play ",
                                "включи музыку", "включи трек"),
        action=action,
    )


def _build_time_leaf():
    def action(t, c):
        if _has(t, "дата", "число", "какой день", "date", "какое сегодня"):
            return {"route": "time", "action": "date", "args": {}}
        return {"route": "time", "action": "now", "args": {}}
    return Leaf(
        "time",
        match=lambda t, c: _has(t, "который час", "сколько времени",
                                "время", "дата", "какое сегодня", "time now"),
        action=action,
    )


def _build_browser_leaf():
    def action(t, c):
        m = re.search(r"(https?://\S+|[\w\-]+\.[a-z]{2,}(?:/\S*)?)", t)
        url = m.group(1) if m else _strip(t, r"\bоткрой\b", r"\bopen\b")
        return {"route": "browser", "action": "open", "args": {"url": url}}
    return Leaf(
        "browser",
        match=lambda t, c: _has(t, "открой сайт", "открой ссылку",
                                "открой http", "open http", "в браузере"),
        action=action,
    )


def _build_app_leaf():
    def action(t, c):
        name = _strip(t, r"\bоткрой\b", r"\bзапусти\b", r"\bopen\b", r"\blaunch\b",
                      r"\bприложение\b")
        return {"route": "app", "action": "launch", "args": {"name": name}}
    return Leaf(
        "app",
        match=lambda t, c: _has(t, "открой", "запусти", "open ", "launch "),
        action=action,
    )


def _build_ask_leaf():
    return Leaf(
        "ask",
        match=lambda t, c: True,
        action=lambda t, c: {"route": "ask", "text": t},
    )


def build_route_tree() -> Selector:
    return Selector("aura_root", [
        _build_control_leaf(),
        _build_power_leaf(),
        _build_music_leaf(),
        _build_time_leaf(),
        _build_browser_leaf(),
        _build_app_leaf(),
        _build_ask_leaf(),
    ])


__all__ = ["build_route_tree"]
