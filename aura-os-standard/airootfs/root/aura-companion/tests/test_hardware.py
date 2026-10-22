"""Тесты hardware detection (ADR-139, 151)."""
from __future__ import annotations


def test_detect_runs():
    from scripts.hardware_detect import detect
    info = detect()
    assert info.os and info.cpu_threads >= 1 and info.ram_total_gb > 0
    assert info.profile in ("minimal", "standard", "powerful")


def test_profiles_yaml():
    import yaml
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "aura/config/hardware_profiles.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert {"minimal", "standard", "powerful"} <= set(data.keys())
    assert data["minimal"]["max_response_words"] == 15


def test_model_selector_low():
    from aura.inference.model_selector import select
    class HW:
        ram_total_gb = 3.0; cpu_threads = 2; has_gpu = False
    cfg = select(HW())
    assert cfg.profile == "minimal"


def test_model_selector_powerful():
    from aura.inference.model_selector import select
    class HW:
        ram_total_gb = 32.0; cpu_threads = 16; has_gpu = True
    cfg = select(HW())
    assert cfg.profile == "powerful"
    assert "7b" in cfg.llm
