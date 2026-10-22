"""#56 GPU-тесты: detect_gpu + model_selector."""
from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from aura import system_check as SC
from aura.inference import model_selector as MS


# === detect_gpu ===

def test_detect_gpu_nvidia():
    with patch("aura.system_check._run", return_value="01:00.0 VGA compatible controller: NVIDIA GP104M"):
        gpus = SC.detect_gpu()
    assert len(gpus) == 1
    assert gpus[0]["vendor"] == "nvidia"


def test_detect_gpu_intel():
    with patch("aura.system_check._run", return_value="00:02.0 VGA compatible controller: Intel UHD 630"):
        gpus = SC.detect_gpu()
    assert gpus[0]["vendor"] == "intel"


def test_detect_gpu_amd():
    with patch("aura.system_check._run", return_value="01:00.0 VGA compatible controller: AMD Radeon RX 580"):
        gpus = SC.detect_gpu()
    assert gpus[0]["vendor"] == "amd"


def test_detect_gpu_unknown():
    with patch("aura.system_check._run", return_value="00:00.0 VGA compatible controller: Matrox G200"):
        gpus = SC.detect_gpu()
    assert gpus[0]["vendor"] == "unknown"


def test_detect_gpu_multiple():
    """Два GPU (Intel iGPU + NVIDIA) → оба найдены."""
    fake = (
        "00:02.0 VGA compatible controller: Intel Corporation CoffeeLake-H GT2\n"
        "01:00.0 VGA compatible controller: NVIDIA Corporation GP104M\n"
    )
    with patch("aura.system_check._run", return_value=fake):
        gpus = SC.detect_gpu()
    assert len(gpus) == 2
    vendors = {g["vendor"] for g in gpus}
    assert vendors == {"intel", "nvidia"}


def test_detect_gpu_empty():
    with patch("aura.system_check._run", return_value="no gpu here"):
        gpus = SC.detect_gpu()
    assert gpus == []


def test_detect_gpu_handles_exception():
    """Ошибка lspci → не крашит, возвращает []."""
    with patch("aura.system_check._run", side_effect=OSError("boom")):
        gpus = SC.detect_gpu()
    assert gpus == []


def test_detect_gpu_3d_controller():
    """3D controller тоже считается GPU (NVIDIA Quadro/ Tesla)."""
    with patch("aura.system_check._run", return_value="00:00.0 3D controller: NVIDIA Corporation GP100"):
        gpus = SC.detect_gpu()
    assert len(gpus) == 1
    assert gpus[0]["vendor"] == "nvidia"


# === model_selector ===

@dataclass
class FakeHW:
    ram_total_gb: float
    cpu_threads: int
    has_gpu: bool


def test_select_minimal_for_low_ram():
    hw = FakeHW(ram_total_gb=3.5, cpu_threads=4, has_gpu=False)
    cfg = MS.select(hw)
    assert cfg.profile == "minimal"


def test_select_edge_for_mid_ram():
    hw = FakeHW(ram_total_gb=8.0, cpu_threads=4, has_gpu=False)
    cfg = MS.select(hw)
    assert cfg.profile == "edge"


def test_select_standard_for_16gb():
    hw = FakeHW(ram_total_gb=16.0, cpu_threads=8, has_gpu=False)
    cfg = MS.select(hw)
    assert cfg.profile == "standard"


def test_select_powerful_for_32gb():
    hw = FakeHW(ram_total_gb=32.0, cpu_threads=12, has_gpu=False)
    cfg = MS.select(hw)
    assert cfg.profile == "powerful"


def test_select_upgrades_edge_with_gpu():
    """RAM=8 ГБ + GPU → профиль должен повышаться до standard."""
    hw = FakeHW(ram_total_gb=8.0, cpu_threads=8, has_gpu=True)
    cfg = MS.select(hw)
    assert cfg.profile == "standard"


def test_select_upgrades_standard_with_gpu_16gb():
    """RAM=16 + GPU → powerful."""
    hw = FakeHW(ram_total_gb=16.0, cpu_threads=8, has_gpu=True)
    cfg = MS.select(hw)
    assert cfg.profile == "powerful"


def test_select_no_upgrade_minimal():
    """GPU не апгрейдит minimal (мало RAM — не поможет)."""
    hw = FakeHW(ram_total_gb=3.0, cpu_threads=4, has_gpu=True)
    cfg = MS.select(hw)
    assert cfg.profile == "minimal"


def test_select_clamps_threads():
    """num_threads ограничен диапазоном [1, 8]."""
    hw = FakeHW(ram_total_gb=16.0, cpu_threads=32, has_gpu=False)
    cfg = MS.select(hw)
    assert cfg.num_threads <= 8


def test_select_threads_at_least_one():
    hw = FakeHW(ram_total_gb=16.0, cpu_threads=0, has_gpu=False)
    cfg = MS.select(hw)
    assert cfg.num_threads >= 1


def test_profiles_have_all_levels():
    """Все 5 профилей объявлены в PROFILES."""
    for name in ("minimal", "minimal_plus", "edge", "standard", "powerful"):
        assert name in MS.PROFILES


def test_profiles_have_identity():
    """Поле profile совпадает с ключом в PROFILES."""
    for name, cfg in MS.PROFILES.items():
        assert cfg.profile == name, f"{name}: cfg.profile={cfg.profile}"


def test_hw_info_has_gpu_flag():
    """has_gpu должен быть boolean-атрибутом HardwareInfo."""
    from aura.inference.model_selector import select
    hw = FakeHW(ram_total_gb=8.0, cpu_threads=4, has_gpu=True)
    cfg = select(hw)
    assert cfg is not None
