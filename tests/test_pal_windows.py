"""PAL Windows: импорт без падения."""
import sys
from unittest.mock import patch


def test_windows_audio_no_pycaw():
    """Без pycaw — не падает, ready=False."""
    with patch.dict(sys.modules, {"pycaw": None}):
        from aura.platform.windows import WindowsAudio
        a = WindowsAudio()
        assert a.ready is False
        assert a.list_sinks() == []


def test_windows_service_imports():
    from aura.platform.windows import WindowsService
    s = WindowsService()
    # notify без исключений
    s.notify("test", "body")


def test_windows_media_imports():
    from aura.platform.windows import WindowsMedia
    m = WindowsMedia()
    assert hasattr(m, "list_players")
