"""#39 Configurator — тесты Textual UI.

Используем run_test() — Textual встроенный headless-режим.
"""
from __future__ import annotations

import pytest

from aura.cockpit import configurator as C


def test_module_imports():
    """Модуль импортируется без ошибок."""
    assert hasattr(C, "ConfiguratorApp")
    assert hasattr(C, "main")
    assert callable(C.main)


def test_tab_classes_exist():
    """Все четыре вкладки объявлены."""
    assert hasattr(C, "ProfileTab")
    assert hasattr(C, "NotificationsTab")
    assert hasattr(C, "KeysTab")
    assert hasattr(C, "AgentsTab")


@pytest.mark.asyncio
async def test_app_starts():
    """Smoke: App запускается и завершается без краша."""
    app = C.ConfiguratorApp()
    async with app.run_test() as pilot:
        # Даём приложению инициализироваться
        await pilot.pause()
        # Проверяем, что все 4 вкладки на месте
        from textual.widgets import TabbedContent, TabPane
        tabs = app.query(TabPane)
        assert len(tabs) == 4


@pytest.mark.asyncio
async def test_profile_tab_renders():
    """Вкладка Профиль рендерится с полями."""
    app = C.ConfiguratorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import Input
        inputs = app.query(Input)
        ids = [i.id for i in inputs]
        assert "input-name" in ids
        assert "input-age" in ids
        assert "input-city" in ids


@pytest.mark.asyncio
async def test_profile_save_button(tmp_path, monkeypatch):
    """Сохранение профиля обновляет profile.json."""
    from aura.core import profile as P
    monkeypatch.setattr(P, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(P, "PROFILE_JSON", tmp_path / "profile.json")

    app = C.ConfiguratorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import Input
        app.query_one("#input-name", Input).value = "test_user"
        app.query_one("#input-city", Input).value = "СПб"
        # Нажимаем кнопку сохранения
        from textual.widgets import Button
        app.query_one("#btn-save", Button).press()
        await pilot.pause()

    # Проверяем, что сохранилось
    saved = P.UserProfile.load()
    assert saved.name == "test_user"
    assert saved.city == "СПб"


@pytest.mark.asyncio
async def test_keys_tab_shows_pubkey(tmp_path, monkeypatch):
    """Вкладка Ключи показывает pubkey."""
    from aura.core import ledger as L
    monkeypatch.setattr(L, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(L, "KEY_DIR", tmp_path / "keys")
    monkeypatch.setattr(L, "PRIV_PATH", tmp_path / "keys/ed25519.key")
    monkeypatch.setattr(L, "PUB_PATH", tmp_path / "keys/ed25519.pub")
    monkeypatch.setattr(L, "LEDGER_DB", tmp_path / "ledger.db")
    L.generate_keypair()

    app = C.ConfiguratorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import Static
        pubkey_widget = app.query_one("#pubkey-display", Static)
        # Textual 0.86+: используем render() вместо renderable
        text = str(pubkey_widget.render())
        assert len(text) >= 40  # base64 от 32 байт = 44


@pytest.mark.asyncio
async def test_notifications_tab_empty(tmp_path, monkeypatch):
    """Вкладка Уведомления не падает при пустой БД."""
    from aura.core import notifications as N
    monkeypatch.setattr(N, "DB", tmp_path / "notif.db")

    app = C.ConfiguratorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        from textual.widgets import DataTable
        table = app.query_one("#notif-table", DataTable)
        assert table is not None


@pytest.mark.asyncio
async def test_bindings_registered():
    """Есть bindings для quit и refresh."""
    app = C.ConfiguratorApp()
    bindings = {b[0] for b in app.BINDINGS}
    assert "q" in bindings
    assert "r" in bindings
