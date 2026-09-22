"""Тесты для aura/status.py."""

from __future__ import annotations

import json

import pytest

from aura import status


@pytest.fixture
def tmp_status(tmp_path, monkeypatch):
    """Перенаправить STATUS_PATH в tmp."""
    p = tmp_path / "aura_status.json"
    monkeypatch.setattr(status, "STATUS_PATH", p)
    return p


def test_set_status_writes_json(tmp_status):
    status.set_status("listening", "тест")
    assert tmp_status.exists()
    data = json.loads(tmp_status.read_text(encoding="utf-8"))
    assert data["state"] == "listening"
    assert data["text"] == "тест"
    assert "ts" in data


def test_set_status_invalid_state(tmp_status):
    status.set_status("garbage", "x")
    data = json.loads(tmp_status.read_text(encoding="utf-8"))
    assert data["state"] == "error"


def test_set_status_truncates_text(tmp_status):
    long = "x" * 500
    status.set_status("thinking", long)
    data = json.loads(tmp_status.read_text(encoding="utf-8"))
    assert len(data["text"]) <= 200


def test_set_status_atomic(tmp_status, monkeypatch):
    """Проверяем, что используется os.replace — не прямой write."""
    called = {"replace": 0}
    real_replace = status.os.replace

    def spy_replace(src, dst):
        called["replace"] += 1
        return real_replace(src, dst)

    monkeypatch.setattr(status.os, "replace", spy_replace)
    status.set_status("idle")
    assert called["replace"] == 1


def test_set_status_swallows_errors(tmp_status, monkeypatch):
    """Ошибки записи не должны ломать Ауру."""
    def boom(*a, **kw):
        raise PermissionError("nope")

    monkeypatch.setattr(status.Path, "write_text", boom)
    status.set_status("idle")  # не должно упасть


def test_clear_status(tmp_status):
    status.set_status("idle")
    assert tmp_status.exists()
    status.clear_status()
    assert not tmp_status.exists()


def test_clear_status_no_file(tmp_status):
    status.clear_status()  # не должно упасть


def test_status_path_env_override(monkeypatch, tmp_path):
    """AURA_STATUS_PATH управляет путём."""
    custom = tmp_path / "custom.json"
    monkeypatch.setenv("AURA_STATUS_PATH", str(custom))
    # Перезагрузить модуль
    import importlib
    importlib.reload(status)
    assert str(status.STATUS_PATH) == str(custom)
    # Вернуть на место
    monkeypatch.delenv("AURA_STATUS_PATH")
    importlib.reload(status)


def test_set_status_paused(tmp_status):
    """Новое состояние paused (Фаза 9.3.1)."""
    status.set_status("paused")
    data = json.loads(tmp_status.read_text(encoding="utf-8"))
    assert data["state"] == "paused"


def test_valid_states_includes_paused():
    assert "paused" in status.VALID_STATES
