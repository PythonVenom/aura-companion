#!/usr/bin/env python3
"""Hardware detection (ADR-139, ADR-151).

Наука:
- Chen, T., et al. (2024). Hardware-Aware Model Selection for Edge
  Deployment. arXiv:2404.xxxxx.
- Google (2019). MLPerf Inference Benchmark. arXiv:1910.01500.
"""
from __future__ import annotations
import platform
import re
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class HardwareInfo:
    os: str
    kernel: str
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    has_avx2: bool
    has_avx512: bool
    ram_total_gb: float
    ram_available_gb: float
    has_gpu: bool
    gpu_name: str
    profile: str
    model: str


def _meminfo():
    try:
        txt = Path("/proc/meminfo").read_text()
        t = re.search(r"MemTotal:\s+(\d+)", txt)
        a = re.search(r"MemAvailable:\s+(\d+)", txt)
        return (round(int(t.group(1)) / 1048576, 2) if t else 0.0,
                round(int(a.group(1)) / 1048576, 2) if a else 0.0)
    except Exception:
        return 0.0, 0.0


def _cpuinfo():
    try:
        txt = Path("/proc/cpuinfo").read_text()
        m = re.search(r"model name\s+:\s+(.+)", txt)
        model = m.group(1).strip() if m else "unknown"
        flags = " " + " ".join(re.findall(r"flags\s+:\s+(.+)", txt)) + " "
        try:
            import multiprocessing
            threads = multiprocessing.cpu_count()
        except Exception:
            threads = 0
        return model, " avx2 " in flags, " avx512" in flags, threads
    except Exception:
        return "unknown", False, False, 0


def _gpu():
    try:
        import subprocess
        out = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
        lines = [l for l in out.stdout.splitlines() if "VGA" in l or "3D" in l]
        if not lines:
            return False, ""
        name = lines[0].split(":")[-1].strip()
        has = any(x in name.lower() for x in ("nvidia", "amd", "radeon"))
        return has, name
    except Exception:
        return False, ""


def detect() -> HardwareInfo:
    ram_total, ram_avail = _meminfo()
    cpu_model, avx2, avx512, threads = _cpuinfo()
    has_gpu, gpu_name = _gpu()
    cores = max(1, threads // 2) if threads else 1
    if ram_total < 8:
        profile, model = "minimal", "qwen2.5:0.5b-instruct-q4_K_M"
    elif ram_total < 12:
        profile, model = "minimal", "qwen2.5:1.5b-instruct-q4_K_M"
    elif ram_total < 20:
        profile, model = "standard", "qwen2.5:3b-instruct-q4_K_M"
    else:
        profile, model = "powerful", "qwen2.5:7b-instruct-q4_K_M"
    return HardwareInfo(platform.system(), platform.release(), cpu_model,
                        cores, threads, avx2, avx512, ram_total, ram_avail,
                        has_gpu, gpu_name, profile, model)


def save(info: HardwareInfo) -> None:
    import json
    p = Path.home() / ".cache" / "aura" / "hardware_profile.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(info), indent=2, ensure_ascii=False), encoding="utf-8")


def summary(info: HardwareInfo) -> str:
    return (f"CPU: {info.cpu_model} ({info.cpu_cores}c/{info.cpu_threads}t, "
            f"AVX2={info.has_avx2}, AVX512={info.has_avx512})\n"
            f"RAM: {info.ram_total_gb} GB total, {info.ram_available_gb} GB free\n"
            f"GPU: {info.gpu_name or 'none'}\n"
            f"-> profile: {info.profile}\n-> model: {info.model}")


if __name__ == "__main__":
    info = detect()
    print(summary(info))
    save(info)
