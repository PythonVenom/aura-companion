"""Idempotent patcher — лечит ошибки v3.0 #5,#7,#8,#11,#12.

Использование:
    from scripts.patches._lib import patch_file
    patch_file("aura/core/orchestrator.py", old, new)
"""
from pathlib import Path


def patch_file(path, old, new, *, marker=None, label=None):
    """
    Идемпотентная замена: если new уже есть — skip.
    Если old нет и new нет — падаем с понятной ошибкой.
    """
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    tag = label or p.name

    if marker and marker in t:
        print(f"[skip] {tag}: уже пропатчен (marker)")
        return False
    if new in t:
        print(f"[skip] {tag}: new уже в файле")
        return False
    if old not in t:
        raise RuntimeError(
            f"[fail] {tag}: old-блок не найден. "
            f"Файл мог измениться или уже пропатчен иначе. "
            f"Покажи 'grep -n <маркер> {path}'"
        )
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print(f"[ok]   {tag}: пропатчен")
    return True
