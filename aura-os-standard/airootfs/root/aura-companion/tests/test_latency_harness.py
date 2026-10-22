"""T082 — тесты latency harness."""
import time
from pathlib import Path

from aura.core import latency_harness


def test_measure_basic(tmp_path, monkeypatch):
    monkeypatch.setattr(latency_harness, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(latency_harness, "RESULTS_FILE", tmp_path / "results.jsonl")
    entry = latency_harness.measure("sleep_50ms", lambda: time.sleep(0.05))
    assert entry["latency_ms"] >= 50
    assert entry["error"] is None


def test_measure_error(tmp_path, monkeypatch):
    monkeypatch.setattr(latency_harness, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(latency_harness, "RESULTS_FILE", tmp_path / "results.jsonl")

    def boom():
        raise ValueError("test")

    entry = latency_harness.measure("boom", boom)
    assert entry["error"] is not None
    assert "ValueError" in entry["error"]


def test_percentile():
    values = list(range(1, 101))  # 1..100
    assert latency_harness.percentile(values, 50) == 50
    assert latency_harness.percentile(values, 95) == 95
    assert latency_harness.percentile(values, 99) == 99


def test_summarize_pass():
    summary = latency_harness.summarize({"fast": [10, 20, 30, 50, 80]})
    assert summary["fast"]["pass"] is True
    assert summary["fast"]["p50"] == 30


def test_summarize_fail():
    summary = latency_harness.summarize({"slow": [500, 1500, 2500, 800, 900]})
    assert summary["slow"]["pass"] is False
    assert summary["slow"]["p99"] >= 1000


def test_run_suite(tmp_path, monkeypatch):
    monkeypatch.setattr(latency_harness, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(latency_harness, "RESULTS_FILE", tmp_path / "results.jsonl")
    suite = {
        "noop": lambda: None,
        "sleep_10ms": lambda: time.sleep(0.01),
    }
    results = latency_harness.run_suite(suite, iterations=3)
    assert len(results["noop"]) == 3
    assert len(results["sleep_10ms"]) == 3


def test_latency_report(tmp_path, monkeypatch):
    monkeypatch.setattr(latency_harness, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(latency_harness, "RESULTS_FILE", tmp_path / "results.jsonl")
    latency_harness.measure("op1", lambda: None)
    latency_harness.measure("op1", lambda: None)
    latency_harness.measure("op2", lambda: None)
    report = latency_harness.latency_report()
    assert report["operations"] == 2
    assert report["total_measurements"] == 3
