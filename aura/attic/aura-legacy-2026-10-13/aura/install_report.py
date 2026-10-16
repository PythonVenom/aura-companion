"""Post-install отчёт: что установлено, что работает.

Вызывается в конце install.sh.
"""
from __future__ import annotations

import shutil
from pathlib import Path


def check_installed() -> dict:
    """Проверить что реально установлено."""
    home = Path.home()
    project = home / "aura_project"

    result = {
        "venv": (project / "venv").exists(),
        "piper": (project / "venv" / "bin" / "piper").exists(),
        "t_one_model": (project / "sherpa-onnx-streaming-t-one-russian-2025-09-08").exists(),
        "voices": (project / "voices").exists(),
        "systemd_unit": (home / ".config" / "systemd" / "user" / "aura.service").exists(),
        "ollama": shutil.which("ollama") is not None,
        "vlc": shutil.which("vlc") is not None,
        "playerctl": shutil.which("playerctl") is not None,
        "pactl": shutil.which("pactl") is not None,
        "firefox": shutil.which("firefox") is not None,
    }

    # Ollama модели
    if result["ollama"]:
        try:
            import subprocess
            r = subprocess.run(["ollama", "list"], capture_output=True,
                                text=True, timeout=3)
            models = r.stdout.lower()
            result["qwen"] = "qwen" in models
            result["nomic"] = "nomic" in models
        except Exception:
            result["qwen"] = False
            result["nomic"] = False

    return result


def format_post_report() -> str:
    """Человекочитаемый отчёт."""
    r = check_installed()
    lines = [
        "╔═══════════════════════════════════════════════════════════╗",
        "║  Aura — отчёт об установке                                ║",
        "╚═══════════════════════════════════════════════════════════╝",
        "",
        "─── Что работает ───",
    ]
    for k, v in r.items():
        mark = "✅" if v else "❌"
        lines.append(f"  {mark} {k}")

    lines.extend([
        "",
        "─── Что делать дальше ───",
    ])
    if not r.get("ollama"):
        lines.append("  ⚠️  Установи Ollama: sudo pacman -S ollama")
    elif not r.get("qwen"):
        lines.append("  ⚠️  Загрузи модель: ollama pull qwen2.5:7b-instruct-q4_K_M")

    if r["systemd_unit"]:
        lines.append("  ✓ Запусти: systemctl --user start aura.service")
        lines.append("  ✓ Логи: journalctl --user -u aura.service -f")

    lines.append("")
    lines.append("  Документация: ~/aura_project/README.md")
    lines.append("  Проверка готовности: docs/adr/010-definition-of-done-beta.md")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    print(format_post_report())
