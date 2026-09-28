"""Config wizard — настройка при первом запуске.

5 вопросов: имя, обращение, характер, юмор, голос.
"""
from __future__ import annotations

from aura import settings


def _ask(prompt: str, default: str = "") -> str:
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    try:
        return input(prompt).strip() or default
    except (EOFError, KeyboardInterrupt):
        return default


def _choose(prompt: str, options: list, default_idx: int = 0) -> str:
    print(f"\n{prompt}")
    for i, o in enumerate(options, 1):
        mark = "*" if i - 1 == default_idx else " "
        print(f"  {mark} {i}. {o}")
    try:
        ans = input(f"Выбор [{default_idx + 1}]: ").strip()
        idx = int(ans) - 1 if ans else default_idx
        return options[idx]
    except (EOFError, KeyboardInterrupt, ValueError, IndexError):
        return options[default_idx]


def run(first_run: bool = True) -> dict:
    print()
    print("=" * 55)
    print("  Aura — первая настройка (5 вопросов)")
    print("=" * 55)

    s = settings.load()
    persona = s.get("persona", {})

    # 1. Имя
    print("\n1. Как называть ассистента?")
    print("   (Аура, Катя, Маруся, Света, Дед, Бабушка...)")
    name = _ask("Имя", persona.get("name", "Аура"))
    persona["name"] = name

    # 2. Обращение
    address = _choose(
        "2. Как обращаться?",
        ["на ты", "на вы"],
        default_idx=0,
    )
    persona["address"] = address.split()[-1]

    # 3. Характер
    style = _choose(
        "3. Характер?",
        ["тёплая", "нейтральная", "строгая"],
        default_idx=0,
    )
    persona["style"] = style

    # 4. Юмор
    humor = _choose(
        "4. Шутить?",
        ["да", "нет"],
        default_idx=0,
    )
    persona["humor"] = humor == "да"

    # 5. Голос
    voice = _choose(
        "5. Голос?",
        ["женский", "мужской", "детский"],
        default_idx=0,
    )
    persona["voice_gender"] = voice

    s["persona"] = persona
    s["wake_word"] = name.lower()
    settings.save(s)

    print()
    print("=" * 55)
    print(f"  Готово!")
    print("=" * 55)
    print(f"  Имя: {persona['name']}")
    print(f"  Обращение: {persona['address']}")
    print(f"  Характер: {persona['style']}")
    print(f"  Юмор: {'да' if persona['humor'] else 'нет'}")
    print(f"  Голос: {persona['voice_gender']}")
    print()
    print(f"  Файл: {settings.SETTINGS_PATH}")
    print()
    return s


if __name__ == "__main__":
    run()
