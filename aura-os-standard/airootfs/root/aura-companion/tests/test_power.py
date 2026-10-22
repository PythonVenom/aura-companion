"""Power agent: subprocess + confirm flow."""
import pytest
from unittest.mock import patch

from aura.agents.power import AgentPower
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture(autouse=True)
def _reset_pending():
    AgentPower._pending = None
    yield
    AgentPower._pending = None


def _req(text):
    return AgentRequest(text=text)


class TestSubprocess:
    def test_shutdown_calls_systemctl_poweroff(self):
        with patch("subprocess.Popen") as popen:
            AgentPower()._shutdown()
            args = popen.call_args[0][0]
            assert args[0] == "systemctl" and "poweroff" in args

    def test_reboot_calls_systemctl_reboot(self):
        with patch("subprocess.Popen") as popen:
            AgentPower()._reboot()
            args = popen.call_args[0][0]
            assert args[0] == "systemctl" and "reboot" in args

    def test_suspend_calls_systemctl_suspend(self):
        with patch("subprocess.Popen") as popen:
            AgentPower()._suspend()
            args = popen.call_args[0][0]
            assert args[0] == "systemctl" and "suspend" in args

    def test_lock_calls_loginctl(self):
        with patch("subprocess.Popen") as popen:
            AgentPower()._lock()
            args = popen.call_args[0][0]
            assert "loginctl" in args[0] or "lock" in " ".join(args)


class TestHandleWithMock:
    @pytest.mark.asyncio
    async def test_shutdown_needs_confirm(self):
        a = AgentPower()
        r = await a.handle(_req("выключи пк"))
        assert AgentPower._pending == "shutdown"
        assert r.status == AgentStatus.OK

    @pytest.mark.asyncio
    async def test_confirm_executes(self):
        a = AgentPower()
        with patch.object(a, "_shutdown", return_value="off") as mock:
            await a.handle(_req("выключи"))
            await a.handle(_req("да"))
            assert mock.called
            assert AgentPower._pending is None

    @pytest.mark.asyncio
    async def test_cancel_does_not_execute(self):
        a = AgentPower()
        with patch.object(a, "_shutdown") as mock:
            await a.handle(_req("выключи"))
            await a.handle(_req("нет"))
            assert not mock.called
            assert AgentPower._pending is None

    @pytest.mark.asyncio
    async def test_lock_no_confirm(self):
        a = AgentPower()
        with patch.object(a, "_lock", return_value="locked"):
            r = await a.handle(_req("заблокируй экран"))
            assert AgentPower._pending is None
            assert r.status == AgentStatus.OK

    @pytest.mark.asyncio
    async def test_reboot_needs_confirm(self):
        a = AgentPower()
        await a.handle(_req("перезагрузи"))
        assert AgentPower._pending == "reboot"

    @pytest.mark.asyncio
    async def test_unknown_returns_not_handled(self):
        a = AgentPower()
        r = await a.handle(_req("привет мир"))
        assert r.status == AgentStatus.NOT_HANDLED
