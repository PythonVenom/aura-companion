#!/usr/bin/env python3
"""Aura Install Wizard — выбор профиля и канала (F-031).

Borderlands-style: Class + Channel + Mods.
Наука: Saltzer & Schroeder 1975 (least privilege),
       Brooks 1975 (first-user-experience),
       Hunicke 2004 (MDA — выбор = engagement).

Запуск:
    python scripts/install_wizard.py         # интерактивно
    python scripts/install_wizard.py --auto elder-stable  # без вопросов
    python scripts/install_wizard.py --auto elder-stable --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROFILES = {
    "elder":   {"name": "Пожилой", "base": "elder", "trees": [], "channel": "stable"},
    "veteran": {"name": "Ветеран/СВО", "base": "veteran", "trees": ["ptsd"], "channel": "stable"},
    "kid":     {"name": "Ребёнок", "base": "kid", "trees": [], "channel": "stable"},
    "blind":   {"name": "Незрячий", "base": "blind", "trees": [], "channel": "stable"},
    "dev":     {"name": "Разработчик", "base": "dev", "trees": [], "channel": "rolling"},
    "guest":   {"name": "Демо/флешка", "base": "guest", "trees": [], "channel": "lts"},
    "auto-electric": {"name": "Автоэлектрик", "base": "auto_electric", "trees": ["auto_vag", "auto_ford", "auto_asia", "auto_china", "auto_russia"], "channel": "stable"},
    "auto-mechanic": {"name": "Автомеханик", "base": "auto_mechanic", "trees": [], "channel": "stable"},
}

CHANNELS = {
    "lts":     "LTS — стабильно, редко обновления, 5 лет поддержки",
    "stable":  "Stable — стабильно, обновления раз в месяц",
    "rolling": "Rolling — новое, обновления ежедневно, возможны баги",
}


def ask_choice(text: str, options: list, default: str | None,
               auto: str | None = None) -> str:
    if auto and auto in options:
        return auto
    print(f"\n{text}")
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    if default:
        print(f"  (по умолчанию: {default})")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nОтмена.")
            sys.exit(0)
        if not raw and default:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        print("Некорректный выбор.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", help="profile-channel (например elder-stable)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    auto_profile = None
    auto_channel = None
    if args.auto:
        parts = args.auto.split("-", 1)
        auto_profile = parts[0] if parts else None
        auto_channel = parts[1] if len(parts) > 1 else None

    print("=" * 60)
    print("  Aura Install Wizard v1")
    print("=" * 60)

    profile = ask_choice(
        "Кому ставим Aura?",
        list(PROFILES.keys()),
        default="elder",
        auto=auto_profile,
    )
    p = PROFILES[profile]
    default_channel = p["channel"]

    channel = ask_choice(
        "Какой канал обновлений?",
        list(CHANNELS.keys()),
        default=default_channel,
        auto=auto_channel or default_channel,
    )

    firefox = ask_choice(
        "Установить Firefox bridge?",
        ["yes", "no"],
        default="yes",
    )

    shell_git = "no"
    if profile == "dev":
        shell_git = ask_choice(
            "Установить shell+git агенты?",
            ["yes", "no"],
            default="no",
        )

    result = {
        "profile": profile,
        "profile_name": p["name"],
        "base_class": p["base"],
        "trees": p["trees"],
        "channel": channel,
        "firefox_bridge": firefox == "yes",
        "shell_git": shell_git == "yes",
    }

    print("\n" + "=" * 60)
    print("  Итог:")
    for k, v in result.items():
        print(f"    {k}: {v}")
    print("=" * 60)

    if args.dry_run:
        print("\n(dry-run — не сохраняю)")
        return

    settings_path = Path.home() / ".config" / "aura" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    settings.update({
        "capability_profile": profile,
        "release_channel": channel,
    })
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n✅ Сохранено: {settings_path}")
    print("Следующий шаг: systemctl --user restart aura.service")


if __name__ == "__main__":
    main()
