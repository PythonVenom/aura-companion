"""ADR-050: push-to-stop через /tmp/aura.stop."""
import time
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from scripts.aura_stop_watcher import watch, STOP_FILE


def test_stop_file_constant():
    assert str(STOP_FILE) == "/tmp/aura.stop"


def test_watch_calls_stop_speaking(monkeypatch):
    """Когда файл появляется — watcher зовёт stop_speaking."""
    import threading
    speaker = MagicMock()
    STOP_FILE.unlink(missing_ok=True)

    t = threading.Thread(target=watch, args=(speaker,), daemon=True)
    t.start()
    time.sleep(0.2)
    STOP_FILE.touch()
    time.sleep(0.4)
    STOP_FILE.unlink(missing_ok=True)

    assert speaker.stop_speaking.called


def test_watch_deletes_stop_file(monkeypatch):
    """Файл удаляется после срабатывания."""
    import threading
    speaker = MagicMock()
    STOP_FILE.touch()

    t = threading.Thread(target=watch, args=(speaker,), daemon=True)
    t.start()
    time.sleep(0.4)

    assert not STOP_FILE.exists()
    STOP_FILE.unlink(missing_ok=True)
