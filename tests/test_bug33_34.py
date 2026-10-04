"""Bug 33 (proactive fresh-fire) + Bug 34 (listener timeout)."""
import time
from aura.agents.proactive import FRESH_FIRE_SECONDS


def test_fresh_fire_constant_reasonable():
    """60 секунд — свежие таймеры; старые не спамят."""
    assert FRESH_FIRE_SECONDS == 60.0
    assert FRESH_FIRE_SECONDS > 10
    assert FRESH_FIRE_SECONDS < 300


def test_timeout_8_in_main():
    """Bug 34: listener timeout >= 8."""
    from pathlib import Path
    s = Path("aura_main.py").read_text(encoding="utf-8")
    assert "listener.listen(timeout=8)" in s
    assert "listener.listen(timeout=5)" not in s
