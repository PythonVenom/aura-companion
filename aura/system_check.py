"""Pre-install system check для Ауры.

Сканирует систему и оценивает:
- CPU, RAM, GPU
- Аудио-сервер (PipeWire/PulseAudio/ALSA)
- Микрофон
- LLM совместимость (RAM ≥ 8 ГБ?)

Использование:
    python -m aura.system_check
    ./install.sh  # вызывает автоматически
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


def _run(cmd: list, timeout: int = 3) -> str:
    """Безопасный запуск команды. Возвращает stdout или ''."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def detect_cpu() -> dict:
    """Определить CPU: модель, ядра, потоки.

    Локаль-независимо: LANG=C lscpu.
    """
    info = {"cores": 0, "threads": 0, "model": ""}
    try:
        env = dict(os.environ)
        env["LANG"] = "C"
        r = subprocess.run(
            ["lscpu"], capture_output=True, text=True, timeout=3, env=env,
        ).stdout
        for line in r.splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            k = k.strip().lower()
            v = v.strip()
            if k == "model name":
                info["model"] = v
            elif k == "cpu(s)":
                try:
                    info["threads"] = int(v)
                except ValueError:
                    pass
            elif k == "core(s) per socket":
                cores_per = int(v)
                sockets = 1
                for ln in r.splitlines():
                    if ln.lower().startswith("socket(s):"):
                        sockets = int(ln.split(":", 1)[1].strip())
                info["cores"] = cores_per * sockets
    except Exception:
        pass
    return info


def detect_ram() -> dict:
    """RAM в ГБ."""
    info = {"total_gb": 0}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    info["total_gb"] = round(kb / 1024 / 1024, 1)
                    break
    except Exception:
        pass
    return info


def detect_gpu() -> list:
    """Список GPU с вендором и моделью."""
    gpus = []
    try:
        r = _run(["lspci"])
        for line in r.splitlines():
            low = line.lower()
            if "vga" in low or "3d controller" in low or "display controller" in low:
                if "nvidia" in low:
                    gpus.append({"vendor": "nvidia", "raw": line})
                elif "amd" in low or "ati" in low or "radeon" in low:
                    gpus.append({"vendor": "amd", "raw": line})
                elif "intel" in low:
                    gpus.append({"vendor": "intel", "raw": line})
                else:
                    gpus.append({"vendor": "unknown", "raw": line})
    except Exception:
        pass
    return gpus


def detect_audio() -> dict:
    """Аудио-сервер и устройства."""
    info = {"server": "unknown", "has_pipewire": False, "has_pulse": False,
            "has_alsa": False, "sinks": 0, "sources": 0}

    if shutil.which("pactl"):
        r = _run(["pactl", "info"])
        if "PipeWire" in r:
            info["server"] = "pipewire"
            info["has_pipewire"] = True
        elif "PulseAudio" in r:
            info["server"] = "pulseaudio"
            info["has_pulse"] = True

        sinks = _run(["pactl", "list", "short", "sinks"])
        sources = _run(["pactl", "list", "short", "sources"])
        info["sinks"] = len([l for l in sinks.splitlines() if l.strip()])
        info["sources"] = len([l for l in sources.splitlines() if l.strip()])

    if shutil.which("aplay") or Path("/dev/snd").exists():
        info["has_alsa"] = True

    return info


def evaluate_llm(ram: dict) -> dict:
    """Оценить: потянет ли LLM qwen2.5:7b Q4 (нужно ~6 ГБ)."""
    total = ram.get("total_gb", 0)
    if total >= 16:
        return {"level": "excellent", "msg": "qwen2.5:7b + запас на 32B"}
    if total >= 8:
        return {"level": "good", "msg": "qwen2.5:7b Q4 работает комфортно"}
    if total >= 6:
        return {"level": "warn", "msg": "qwen2.5:7b впритык, лучше Q3"}
    if total >= 4:
        return {"level": "limited", "msg": "только Q2 или без LLM"}
    return {"level": "fail", "msg": "недостаточно RAM, LLM не запустится"}


def full_check() -> dict:
    """Полная диагностика. Возвращает всё."""
    cpu = detect_cpu()
    ram = detect_ram()
    gpu = detect_gpu()
    audio = detect_audio()
    llm = evaluate_llm(ram)

    # Overall
    issues = []
    if ram["total_gb"] < 2:  # AURA_RAM_FIX_V1 — 4→2 (реально 1 ГБ + LLM 1.5)
        issues.append("RAM < 2 ГБ")
    if not audio["has_alsa"] and not audio["has_pipewire"]:
        issues.append("аудио-сервер не найден")
    if audio["sources"] == 0:
        issues.append("микрофон не найден")

    overall = "ok" if not issues else "warn" if len(issues) <= 2 else "fail"

    return {
        "cpu": cpu, "ram": ram, "gpu": gpu, "audio": audio, "llm": llm,
        "overall": overall, "issues": issues,
        "platform": {
            "os": platform.system(),
            "distro": _distro_name(),
            "python": platform.python_version(),
        },
    }


def _distro_name() -> str:
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return platform.system()


def format_report() -> str:
    """Человекочитаемый отчёт для установщика."""
    r = full_check()
    lines = [
        "╔═══════════════════════════════════════════════════════════╗",
        "║  Aura — проверка системы                                  ║",
        "╚═══════════════════════════════════════════════════════════╝",
        "",
        f"ОС: {r['platform']['distro']} ({r['platform']['os']})",
        f"Python: {r['platform']['python']}",
        "",
        "─── Процессор ───",
        f"  {r['cpu']['model'] or 'неизвестно'}",
        f"  Ядер: {r['cpu']['cores']}, потоков: {r['cpu']['threads']}",
        "",
        "─── Память ───",
        f"  {r['ram']['total_gb']} ГБ",
        f"  Оценка LLM: {r['llm']['level'].upper()} — {r['llm']['msg']}",
        "",
        "─── GPU ───",
    ]
    if r["gpu"]:
        for g in r["gpu"]:
            lines.append(f"  [{g['vendor']}] {g['raw'][:70]}")
    else:
        lines.append("  не найдено (только CPU-режим)")

    lines.extend([
        "",
        "─── Аудио ───",
        f"  Сервер: {r['audio']['server']}",
        f"  Sinks: {r['audio']['sinks']}, Sources: {r['audio']['sources']}",
        "",
        "─── Итог ───",
    ])
    if r["overall"] == "ok":
        lines.append("  ✅ Система готова. Установка возможна.")
    elif r["overall"] == "warn":
        lines.append("  ⚠️  Есть предупреждения:")
        for i in r["issues"]:
            lines.append(f"     • {i}")
        lines.append("  Установка возможна, но некоторые модули будут ограничены.")
    else:
        lines.append("  ❌ Система не готова:")
        for i in r["issues"]:
            lines.append(f"     • {i}")
        lines.append("  Установка может быть затруднена.")

    lines.append("")
    return "\n".join(lines)


def save_report(path: Path | None = None) -> Path:
    """Сохранить отчёт в файл."""
    if path is None:
        path = Path.home() / "aura_private" / "install_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_report(), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(format_report())
