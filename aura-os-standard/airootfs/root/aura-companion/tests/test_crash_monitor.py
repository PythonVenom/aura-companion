"""T081 — тесты crash monitor."""
import json
import time
from pathlib import Path
from unittest.mock import patch

from aura.core import crash_monitor


def test_mark_and_uptime(tmp_path, monkeypatch):
    monkeypatch.setattr(crash_monitor, "STATE_DIR", tmp_path)
    monkeypatch.setattr(crash_monitor, "HEARTBEAT_FILE", tmp_path / "heartbeat.json")
    monkeypatch.setattr(crash_monitor, "CRASH_LOG", tmp_path / "crashes.jsonl")
    monkeypatch.setattr(crash_monitor, "START_FILE", tmp_path / "started_at.txt")
    crash_monitor.mark_start()
    assert crash_monitor.uptime_days() >= 0
    assert crash_monitor.last_heartbeat_age_sec() < 10


def test_record_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(crash_monitor, "STATE_DIR", tmp_path)
    monkeypatch.setattr(crash_monitor, "CRASH_LOG", tmp_path / "crashes.jsonl")
    monkeypatch.setattr(crash_monitor, "START_FILE", tmp_path / "started_at.txt")
    monkeypatch.setattr(crash_monitor, "HEARTBEAT_FILE", tmp_path / "heartbeat.json")
    crash_monitor.mark_start()
    try:
        raise ValueError("test crash")
    except ValueError as e:
        crash_monitor.record_crash(e, "test")
    assert crash_monitor.crash_count() == 1
    report = crash_monitor.stability_report()
    assert report["crashes_30d"] == 1
    assert report["target"]["healthy"] is False


def test_stability_healthy(tmp_path, monkeypatch):
    monkeypatch.setattr(crash_monitor, "STATE_DIR", tmp_path)
    monkeypatch.setattr(crash_monitor, "CRASH_LOG", tmp_path / "crashes.jsonl")
    monkeypatch.setattr(crash_monitor, "START_FILE", tmp_path / "started_at.txt")
    monkeypatch.setattr(crash_monitor, "HEARTBEAT_FILE", tmp_path / "heartbeat.json")
    crash_monitor.mark_start()
    report = crash_monitor.stability_report()
    assert report["crashes_30d"] == 0
    # uptime < 30 дней → не healthy (правильно — ещё наблюдаем)


def test_mtbf(tmp_path, monkeypatch):
    monkeypatch.setattr(crash_monitor, "STATE_DIR", tmp_path)
    monkeypatch.setattr(crash_monitor, "CRASH_LOG", tmp_path / "crashes.jsonl")
    monkeypatch.setattr(crash_monitor, "START_FILE", tmp_path / "started_at.txt")
    monkeypatch.setattr(crash_monitor, "HEARTBEAT_FILE", tmp_path / "heartbeat.json")
    crash_monitor.mark_start()
    assert crash_monitor.mtbf_days() == float("inf")


def test_reset(tmp_path, monkeypatch):
    monkeypatch.setattr(crash_monitor, "STATE_DIR", tmp_path)
    monkeypatch.setattr(crash_monitor, "CRASH_LOG", tmp_path / "crashes.jsonl")
    monkeypatch.setattr(crash_monitor, "START_FILE", tmp_path / "started_at.txt")
    monkeypatch.setattr(crash_monitor, "HEARTBEAT_FILE", tmp_path / "heartbeat.json")
    crash_monitor.mark_start()
    crash_monitor.reset()
    assert not crash_monitor.START_FILE.exists()
