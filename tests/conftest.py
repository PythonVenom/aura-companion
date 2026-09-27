"""Общие фикстуры для тестов Aura."""
import pytest

from aura.agents import media_state


@pytest.fixture(autouse=True)
def _clean_media_state():
    """Bug 14: тесты не должны зависеть от live /tmp/aura_media_state.json."""
    media_state.clear()
    yield
    media_state.clear()
