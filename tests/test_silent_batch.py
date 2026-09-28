"""Bug 30: silent для окна/столы/вкладки/приложения (ADR-048)."""
import asyncio
import pytest
from aura.agents.app_launcher import AgentAppLauncher
from aura.agents.window_control import AgentWindowControl
from aura.agents.browser_tabs import AgentBrowserTabs
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.mark.parametrize("cmd,expected_silent", [
    ("открой firefox", True),
    ("запусти telegram", True),
    ("покажи приложения", False),
])
def test_app_launcher_silent(cmd, expected_silent):
    a = AgentAppLauncher()
    r = asyncio.run(a.handle(AgentRequest(text=cmd)))
    if r.status == AgentStatus.OK:
        assert r.silent is expected_silent, f"{cmd!r} silent={r.silent}"


@pytest.mark.parametrize("cmd", [
    "сверни окно", "разверни окно", "закрой окно",
])
def test_window_control_silent(cmd):
    a = AgentWindowControl()
    r = asyncio.run(a.handle(AgentRequest(text=cmd)))
    if r.status == AgentStatus.OK:
        assert r.silent is True, f"{cmd!r} silent={r.silent}"


@pytest.mark.parametrize("cmd", [
    "какие вкладки", "следующая вкладка", "переключи на youtube",
])
def test_browser_tabs_silent(cmd):
    a = AgentBrowserTabs()
    r = asyncio.run(a.handle(AgentRequest(text=cmd)))
    if r.status == AgentStatus.OK and cmd != "какие вкладки":
        assert r.silent is True, f"{cmd!r} silent={r.silent}"
