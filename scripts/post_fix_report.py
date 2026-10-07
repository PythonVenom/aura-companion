#!/usr/bin/env python3
"""Post-fix report — Аура говорит после коммита (F-038).

Наука: Duhigg 2012 (habit loop), Skinner 1938 (reinforcement),
       Nielsen 1993 (visibility of system status).

Логика:
- Обычно: молчит
- После коммита: говорит результат (успех / провал)
- При провале: причина + что делать
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO = "/home/pythonvenom/aura_project"
VENV_PY = f"{REPO}/venv/bin/python3"


def run(cmd: list, cwd: str = REPO, timeout: int = 60) -> tuple:
    """Возвращает (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=cwd,
        )
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)


def check_ruff() -> tuple:
    rc, out, _ = run([VENV_PY, "-m", "ruff", "check", "aura/"], timeout=30)
    return rc == 0, out


def check_pytest() -> tuple:
    rc, out, _ = run(
        [VENV_PY, "-m", "pytest", "tests/", "-q", "--tb=no"],
        timeout=120,
    )
    # Парсим "1555 passed"
    count = 0
    failed = 0
    for line in out.splitlines():
        if "passed" in line:
            parts = line.split()
            for i, p in enumerate(parts):
                if "passed" in p and i > 0:
                    try:
                        count = int(parts[i - 1])
                    except ValueError:
                        pass
                if "failed" in p and i > 0:
                    try:
                        failed = int(parts[i - 1])
                    except ValueError:
                        pass
    return rc == 0, count, failed


def get_last_commit() -> tuple:
    rc, out, _ = run(["git", "log", "-1", "--pretty=%h|%s"], timeout=5)
    if rc != 0:
        return "?", "?"
    parts = out.strip().split("|", 1)
    return parts[0] if parts else "?", parts[1] if len(parts) > 1 else "?"


def say(text: str) -> None:
    """Говорим ГОЛОСОМ АУРЫ (Piper + Ирина), не чужим.
    
    Наука: раздел 23 промта — не подменять Ауру. 
           Раздел 25 — минимальное изменение.
    """
    # Способ 1: через speaker агента Ауры (Piper + Ирина)
    try:
        from aura.agents.speaker import AgentSpeaker
        sp = AgentSpeaker()
        sp.say(text)
        return
    except Exception as e:
        print(f"⚠️ [Speaker] {e}")
    
    # Fallback: Piper напрямую
    import shutil
    voice = Path(REPO) / "voices" / "ru_RU-irina-medium.onnx"
    if shutil.which("piper") and voice.exists():
        try:
            r = subprocess.run(
                ["piper", "--model", str(voice),
                 "--output_file", "/tmp/aura_say.wav"],
                input=text, text=True, capture_output=True,
                timeout=30, cwd=REPO,
            )
            if r.returncode == 0:
                subprocess.run(
                    ["aplay", "-q", "/tmp/aura_say.wav"],
                    timeout=30, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
        except Exception:
            pass
    
    print(f"🔊 [TTS fallback] {text}")


def main() -> None:
    silent = "--silent" in sys.argv
    speak = "--speak" in sys.argv
    commit, msg = get_last_commit()

    # 1. Проверка ruff
    ruff_ok, ruff_out = check_ruff()

    # 2. Проверка pytest
    pytest_ok, passed, failed = check_pytest()

    # 3. Формируем отчёт
    if ruff_ok and pytest_ok:
        text = f"Система стабильна. Обновления встали. Тестов: {passed}."
        status = "✅"
    else:
        parts = ["Ошибка обновления. Не встали."]
        if not ruff_ok:
            parts.append("Ruff нашёл проблемы.")
        if not pytest_ok:
            parts.append(f"Тестов упало: {failed}.")
        text = " ".join(parts)
        status = "❌"

    # 4. Печатаем всегда
    print(f"{status} [F-038] Аура: {text}")
    print(f"   commit: {commit} | {msg[:50]}")

    # 5. Говорим только если --speak и не silent
    if speak and not silent:
        say(text)


if __name__ == "__main__":
    main()
