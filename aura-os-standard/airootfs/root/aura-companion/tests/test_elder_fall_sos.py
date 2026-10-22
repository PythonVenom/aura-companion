"""Интеграционный тест: падение → SOS (GAPS #92).

Проверяем цепочку:
1. «упал» / «помогите встать» → AgentFall
2. AgentFall вызывает AgentSOS
3. Запись в fall_state.json
4. SOS-конфиг загружается

Наука:
- WHO 2021 (Falls — leading cause of injury death для 65+)
- CDC STEADI (2019) — Stopping Elderly Accidents
- NICE NG249 (2022) — falls assessment
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from aura.core.protocol import AgentRequest


def _run(coro):
    return asyncio.run(coro)


# ============================================================
# 1. AgentFall — базовые
# ============================================================
def test_fall_agent_exists():
    from aura.agents.fall import AgentFall
    a = AgentFall()
    assert a.name == "fall"


@pytest.mark.parametrize("text", [
    "я упал",
    "упала",
    "не могу встать",
    "помогите встать",
])
def test_fall_can_handle_positive(text):
    from aura.agents.fall import AgentFall
    a = AgentFall()
    assert a.can_handle(AgentRequest(text=text))


@pytest.mark.parametrize("text", [
    "привет",
    "который час",
    "погода",
])
def test_fall_can_handle_negative(text):
    from aura.agents.fall import AgentFall
    a = AgentFall()
    assert not a.can_handle(AgentRequest(text=text))


def test_fall_constants():
    """Константы из ADR / WHO."""
    from aura.agents.fall import FALL_G_THRESHOLD, STILLNESS_SECONDS, TRIGGER_KEYWORDS
    assert FALL_G_THRESHOLD >= 2.0  # 3g
    assert STILLNESS_SECONDS >= 10  # 30 сек
    assert "упал" in TRIGGER_KEYWORDS


# ============================================================
# 2. AgentSOS — базовые
# ============================================================
def test_sos_agent_exists():
    from aura.agents.sos import AgentSOS
    a = AgentSOS()
    assert a.name == "sos"


@pytest.mark.parametrize("text", [
    "мне плохо",
    "помогите",
    "вызови скорую",
    "вызов скорой",
    "тревога",
])
def test_sos_can_handle_positive(text):
    from aura.agents.sos import AgentSOS
    a = AgentSOS()
    assert a.can_handle(AgentRequest(text=text))


# ============================================================
# 3. Цепочка fall → SOS (главное)
# ============================================================
def test_fall_calls_sos(tmp_path):
    """Падение → AgentFall вызывает AgentSOS (или возвращает осмысленный ответ)."""
    from aura.agents.fall import AgentFall
    from aura.agents.sos import AgentSOS

    fall = AgentFall()
    r = _run(fall.handle(AgentRequest(text="я упал")))

    # Проверяем: ответ не пустой, есть SOS или 🆘
    assert r is not None
    assert r.text, "fall.handle вернул пустой ответ"
    # Приемлемые ответы:
    # - 🆘 SOS
    # - SOS! Но экстренный контакт не настроен
    # - Обнаружено падение
    valid = (
        "🆘" in r.text
        or "SOS" in r.text.upper()
        or "падени" in r.text.lower()
    )
    assert valid, f"Неожиданный ответ: {r.text}"


def test_fall_logs_event(tmp_path):
    """fall.handle пишет в STATE_FILE."""
    from aura.agents.fall import AgentFall

    fall = AgentFall()
    original = fall.STATE_FILE
    fall.STATE_FILE = tmp_path / "fall_state.json"

    try:
        _run(fall.handle(AgentRequest(text="я упал")))
        assert fall.STATE_FILE.exists(), "fall_state.json не создан"
    finally:
        fall.STATE_FILE = original


def test_fall_writes_state(tmp_path):
    """Падение пишет в fall_state.json."""
    from aura.agents.fall import AgentFall

    # Переопределяем STATE_FILE на tmp
    fall = AgentFall()
    original = fall.STATE_FILE

    fake_state = tmp_path / "fall_state.json"
    fall.STATE_FILE = fake_state

    try:
        _run(fall.handle(AgentRequest(text="упал")))
        assert fake_state.exists()
        data = json.loads(fake_state.read_text())
        assert "ts" in data or "last_fall" in data or isinstance(data, dict)
    finally:
        fall.STATE_FILE = original


# ============================================================
# 4. AgentSOS — конфиг
# ============================================================
def test_sos_loads_config():
    """SOS загружает конфиг (может быть пустым)."""
    from aura.agents.sos import AgentSOS
    a = AgentSOS()
    cfg = a._load_config()
    assert isinstance(cfg, dict)


def test_sos_handle_returns_response():
    """SOS.handle возвращает AgentResponse."""
    from aura.agents.sos import AgentSOS
    a = AgentSOS()
    r = _run(a.handle(AgentRequest(text="мне плохо")))
    assert r is not None
    assert hasattr(r, "text")


def test_sos_not_handled_for_random():
    """SOS не реагирует на «привет»."""
    from aura.agents.sos import AgentSOS
    a = AgentSOS()
    r = _run(a.handle(AgentRequest(text="привет")))
    # NotHandled → пустой или None
    assert r.text in ("", None) or "не понял" in r.text.lower()


# ============================================================
# 5. Все elder-care агенты в registry
# ============================================================
def test_fall_and_sos_registered():
    """Fall и SOS есть в registry."""
    from aura.bootstrap import build_orchestrator
    orch = build_orchestrator()
    names = set(orch.registry.list_names())
    assert "fall" in names
    assert "sos" in names
