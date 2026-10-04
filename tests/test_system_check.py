"""System check: pre-install диагностика Ауры."""
from unittest.mock import MagicMock, patch

from aura import system_check as sc


def test_detect_cpu_returns_dict():
    info = sc.detect_cpu()
    assert isinstance(info, dict)
    assert "cores" in info or "model" in info


def test_detect_ram_returns_gb():
    info = sc.detect_ram()
    assert isinstance(info, dict)
    assert "total_gb" in info
    assert info["total_gb"] > 0


def test_detect_gpu_returns_list():
    info = sc.detect_gpu()
    assert isinstance(info, list)


def test_detect_audio_returns_dict():
    info = sc.detect_audio()
    assert isinstance(info, dict)
    assert "server" in info


def test_evaluate_llm_ram_8gb_passes():
    result = sc.evaluate_llm({"total_gb": 16})
    assert result["level"] in ("good", "excellent")


def test_evaluate_llm_ram_4gb_warns():
    result = sc.evaluate_llm({"total_gb": 4})
    assert result["level"] in ("warn", "limited")


def test_evaluate_llm_ram_2gb_fails():
    result = sc.evaluate_llm({"total_gb": 2})
    assert result["level"] == "fail"


def test_format_report_returns_string():
    report = sc.format_report()
    assert isinstance(report, str)
    assert "Aura" in report or "Аура" in report


def test_full_check_returns_all_keys():
    result = sc.full_check()
    assert "cpu" in result
    assert "ram" in result
    assert "gpu" in result
    assert "audio" in result
    assert "llm" in result
    assert "overall" in result
