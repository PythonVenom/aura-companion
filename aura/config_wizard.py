"""Config wizard — настройка при первом запуске.

Запуск:
    python -m aura.config_wizard
"""
from __future__ import annotations

from aura import settings


def _ask(prompt: str, default: str = "") -> str:
    """Спросить значение с default."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    try:
        answer = input(prompt).strip()
        return answer or default
    except (EOFError, KeyboardInterrupt):
        return default


def run(first_run: bool = True) -> dict:
    """Интерактивная настройка. Возвращает финальные настройки."""
    print()
    print("=" * 50)
    print("  Aura — первая настройка")
    print("=" * 50)
    print()
    print("3 вопроса — 30 секунд.")
    print()

    s = settings.load()

    # 1. Имя ассистента
    print("1. Как называть ассистента?")
    print("   (по умолчанию: Аура. Можно: Катя, Маруся, Света, Дед...)")
    new_wake = _ask("Имя", s.get("wake_word", "аура"))
    s["wake_word"] = new_wake.lower()
    print()

    # 2. Скорость речи
    print("2. Скорость речи (0.5=медленно, 2.0=быстро)")
    new_speed = _ask("Скорость", str(s.get("tts_speed", 1.0)))
    try:
        s["tts_speed"] = float(new_speed)
    except ValueError:
        pass
    print()

    # 3. Громкость
    print("3. Громкость голоса (0–100)")
    new_vol = _ask("Громкость", str(s.get("volume", 100)))
    try:
        s["volume"] = int(new_vol)
    except ValueError:
        pass
    print()

    settings.save(s)

    print("=" * 50)
    print("  Готово!")
    print("=" * 50)
    print(f"  Имя: {s['wake_word']}")
    print(f"  Скорость: {s['tts_speed']}")
    print(f"  Громкость: {s['volume']}")
    print()
    print(f"  Файл: {settings.SETTINGS_PATH}")
    print("  Изменить: aura settings set KEY VALUE")
    print()

    return s


if __name__ == "__main__":
    run()
