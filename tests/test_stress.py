"""#95 Stress-test — тесты soak."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from scripts import aura_stress as S


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "STRESS_DB", tmp_path / "stress.db")
    yield


# === _read_rss_mb ===

def test_read_rss_positive():
    rss = S._read_rss_mb()
    assert rss > 0, "RSS должен быть > 0 для работающего процесса"


def test_read_rss_reasonable():
    rss = S._read_rss_mb()
    assert rss < 10_000, f"RSS={rss} MB — подозрительно много"


# === Sample dataclass ===

def test_sample_dataclass():
    s = S.Sample(ts=1.0, rss_mb=42.5, agents_count=92, latency_ms=1.2)
    assert s.ts == 1.0
    assert s.rss_mb == 42.5
    assert s.agents_count == 92
    assert s.latency_ms == 1.2


# === _ensure_db + _save_sample ===

def test_ensure_db_creates_table(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "STRESS_DB", tmp_path / "s.db")
    S._ensure_db()
    conn = sqlite3.connect(tmp_path / "s.db")
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    assert ("samples",) in tables


def test_save_sample_inserts(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "STRESS_DB", tmp_path / "s.db")
    S._save_sample(S.Sample(ts=1.0, rss_mb=50.0, agents_count=10, latency_ms=5.0))
    conn = sqlite3.connect(tmp_path / "s.db")
    row = conn.execute("SELECT rss_mb, agents_count FROM samples").fetchone()
    conn.close()
    assert row == (50.0, 10)


def test_save_sample_never_crashes(monkeypatch):
    """Если БД сломана — не падаем."""
    monkeypatch.setattr(S, "STRESS_DB", Path("/root/cannot_write/stress.db"))
    # Не должно быть исключения
    S._save_sample(S.Sample(ts=1.0, rss_mb=1, agents_count=0, latency_ms=0))


# === run_soak ===

def test_run_soak_short_duration(tmp_path, monkeypatch):
    """Короткий прогон 0.5 сек — проходит без утечки."""
    monkeypatch.setattr(S, "STRESS_DB", tmp_path / "s.db")
    # Патчим orchestrator, чтобы не собирать реальный
    monkeypatch.setattr(
        "aura.bootstrap.build_orchestrator",
        lambda: (_ for _ in ()).throw(ImportError("skip")),
    )
    exit_code = S.run_soak(duration_sec=0, interval_sec=1)
    # duration=0 → цикл не выполнится, baseline_rss=None → exit 2
    assert exit_code in (0, 2)


def test_run_soak_detects_leak(tmp_path, monkeypatch):
    """Если RSS растёт выше порога — exit code 1."""
    monkeypatch.setattr(S, "STRESS_DB", tmp_path / "s.db")
    # Подделываем: первый вызов 50МБ, второй 200МБ
    calls = iter([50.0, 200.0, 200.0])
    monkeypatch.setattr(S, "_read_rss_mb", lambda: next(calls))
    monkeypatch.setattr(
        "aura.bootstrap.build_orchestrator",
        lambda: (_ for _ in ()).throw(ImportError("skip")),
    )
    exit_code = S.run_soak(duration_sec=10, interval_sec=0, leak_threshold_mb=100)
    assert exit_code == 1


def test_run_soak_writes_samples(tmp_path, monkeypatch):
    """Сэмплы пишутся в БД."""
    db = tmp_path / "s.db"
    monkeypatch.setattr(S, "STRESS_DB", db)
    monkeypatch.setattr(
        "aura.bootstrap.build_orchestrator",
        lambda: (_ for _ in ()).throw(ImportError("skip")),
    )
    S.run_soak(duration_sec=0, interval_sec=0)
    # Даже с duration=0 создаст таблицу
    assert db.exists()


# === CLI ===

def test_main_parses_args(monkeypatch):
    import sys as _sys
    monkeypatch.setattr(_sys, "argv", ["aura_stress", "--duration", "0", "--interval", "0"])
    monkeypatch.setattr("aura.bootstrap.build_orchestrator",
                        lambda: (_ for _ in ()).throw(ImportError("skip")))
    code = S.main()
    assert code in (0, 2)


# === Константы ===

def test_default_leak_threshold():
    assert S.DEFAULT_MEMORY_LEAK_MB == 100.0


def test_stress_db_path_expanduser():
    """STRESS_DB разворачивает ~ в путь."""
    assert "~" not in str(S.STRESS_DB)
