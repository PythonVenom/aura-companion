"""stability_report.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from stability_report import analyze, format_report


def test_analyze_empty(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text("start_ts,duration_h,service,rss_mb,cpu_pct,errors_5min,restarts\n")
    result = analyze(str(p))
    assert result == {"error": "CSV пуст"}


def test_analyze_ok(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text(
        "start_ts,duration_h,service,rss_mb,cpu_pct,errors_5min,restarts\n"
        "2026-09-28T00:00,24,active,150,5.0,0,0\n"
        "2026-09-28T00:01,24,active,152,6.0,0,0\n"
        "2026-09-28T00:02,24,active,148,4.5,0,0\n"
    )
    r = analyze(str(p))
    assert r["iterations"] == 3
    assert r["service_active_pct"] == 100.0
    assert r["restarts_max"] == 0
    assert r["rss_mb"]["avg"] == 150.0


def test_analyze_with_errors(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text(
        "start_ts,duration_h,service,rss_mb,cpu_pct,errors_5min,restarts\n"
        "2026-09-28T00:00,24,active,150,5.0,2,0\n"
        "2026-09-28T00:01,24,active,152,6.0,1,1\n"
    )
    r = analyze(str(p))
    assert r["errors_total"] == 3
    assert r["restarts_max"] == 1


def test_format_pass(tmp_path):
    stats = {
        "iterations": 100,
        "rss_mb": {"min": 100, "max": 200, "avg": 150},
        "cpu_pct": {"min": 1.0, "max": 10.0, "avg": 5.0},
        "errors_total": 0,
        "restarts_max": 0,
        "service_active_pct": 100.0,
    }
    out = format_report(stats)
    assert "PASS" in out


def test_format_attention():
    stats = {
        "iterations": 100,
        "rss_mb": {"min": 100, "max": 3000, "avg": 2500},
        "cpu_pct": {"min": 1.0, "max": 10.0, "avg": 5.0},
        "errors_total": 50,
        "restarts_max": 5,
        "service_active_pct": 80.0,
    }
    out = format_report(stats)
    assert "ATTENTION" in out
