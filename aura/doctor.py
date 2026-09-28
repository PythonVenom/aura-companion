"""aura doctor — диагностика одной командой.

Проверяет: сервис, ollama, T-one, Piper, PipeWire, Firefox bridge, settings.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def _check(label: str, ok: bool, hint: str = "") -> tuple[str, bool]:
    mark = "✅" if ok else "❌"
    msg = f"  {mark} {label}"
    if not ok and hint:
        msg += f"  →  {hint}"
    return msg, ok


def check_all() -> tuple[list[str], int, int]:
    """Возвращает (lines, ok_count, total_count)."""
    lines = []
    ok_count = 0
    total = 0

    # 1. Сервис
    total += 1
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "aura.service"],
            capture_output=True, text=True, timeout=5,
        )
        ok = r.stdout.strip() == "active"
    except Exception:
        ok = False
    msg, ok = _check("aura.service active", ok, "systemctl --user start aura.service")
    lines.append(msg); ok_count += ok

    # 2. Ollama
    total += 1
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            data = json.loads(r.read())
            models = [m["name"] for m in data.get("models", [])]
            ok = any("qwen" in m for m in models)
            if ok:
                lines.append(f"  ✅ Ollama + {len(models)} моделей")
            else:
                lines.append("  ❌ Ollama: qwen не найден  →  ollama pull qwen2.5:7b")
    except Exception:
        lines.append("  ❌ Ollama недоступен  →  systemctl --user start ollama")
    ok_count += ok

    # 3. T-one (ASR) — проверим бинарь
    total += 1
    ok = shutil.which("t-one") is not None or Path("/usr/local/bin/t-one").exists()
    msg, ok = _check("T-one (ASR)", ok, "см. docs/install-advanced.md")
    lines.append(msg); ok_count += ok

    # 4. Piper (TTS)
    total += 1
    ok = shutil.which("piper") is not None
    msg, ok = _check("Piper (TTS)", ok, "pacman -S piper-tts / pip install piper-tts")
    lines.append(msg); ok_count += ok

    # 5. PipeWire
    total += 1
    ok = shutil.which("pipewire") is not None or shutil.which("pw-cli") is not None
    msg, ok = _check("PipeWire", ok, "systemctl --user start pipewire")
    lines.append(msg); ok_count += ok

    # 6. Firefox bridge (native messaging manifest)
    total += 1
    nmm = Path.home() / ".mozilla" / "native-messaging-hosts"
    ok = nmm.exists() and any(nmm.iterdir()) if nmm.exists() else False
    msg, ok = _check("Firefox bridge", ok, "bash scripts/install_extension.sh")
    lines.append(msg); ok_count += ok

    # 7. settings.json
    total += 1
    from aura import settings
    ok = settings.SETTINGS_PATH.exists()
    msg, ok = _check(f"settings.json ({settings.SETTINGS_PATH})", ok,
                     "aura settings-reset / config_wizard")
    lines.append(msg); ok_count += ok

    # 8. Агентов в bootstrap
    total += 1
    try:
        from aura.bootstrap import build_orchestrator
        orch = build_orchestrator()
        n = len(orch)
        ok = n >= 30
        msg = f"  {'✅' if ok else '❌'} Агентов: {n}"
        lines.append(msg); ok_count += ok
    except Exception as e:
        lines.append(f"  ❌ Bootstrap: {e}")
        ok_count += 0

    return lines, ok_count, total


def main() -> int:
    print("🩺 aura doctor — диагностика")
    print("=" * 50)
    lines, ok, total = check_all()
    for l in lines:
        print(l)
    print("=" * 50)
    print(f"  {ok}/{total} OK")
    if ok == total:
        print("  ✨ Всё работает. Готово к запуску.")
        return 0
    print("  ⚠️  Есть проблемы. См. docs/troubleshooting.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
