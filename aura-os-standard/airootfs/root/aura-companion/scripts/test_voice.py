"""Живое тестирование голосовых фич AURA (F-074, STT, Ducking).

Запуск:
    export PYTHONPATH=$PWD
    ./venv/bin/python scripts/test_voice.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def test_voice_profiles() -> bool:
    section("F-074: Voice Profiles")
    try:
        from aura import voice_profiles as vp
        profiles = vp.list_profiles()
        print(f"  Найдено профилей: {len(profiles)}")
        for p in profiles:
            print(f"    - {p.name}")
        if not profiles:
            print("  ⚠️  Профилей нет. Запишите: ./venv/bin/python scripts/test_voice.py --enroll")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def test_stt_available() -> bool:
    section("STT: AgentListener")
    try:
        from aura.agents.listener import AgentListener
        lst = AgentListener()
        print(f"  ✅ AgentListener загружен: {type(lst).__name__}")
        print(f"  Методы: listen={hasattr(lst, 'listen')}, pause={hasattr(lst, 'pause')}")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def test_ducker_available() -> bool:
    section("Ducking: AgentMusicDucker")
    try:
        from aura.agents.music_ducker import AgentMusicDucker
        d = AgentMusicDucker()
        print("  ✅ AgentMusicDucker загружен")
        sinks = d._get_all_active_sink_inputs()
        print(f"  Активных sink inputs: {len(sinks)}")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def main() -> int:
    print("🛸 AURA Voice Test Suite")
    results = {
        "F-074 Voice Profiles": test_voice_profiles(),
        "STT Listener": test_stt_available(),
        "Ducking": test_ducker_available(),
    }
    section("ИТОГ")
    ok = sum(1 for v in results.values() if v)
    for name, v in results.items():
        print(f"  {'✅' if v else '❌'} {name}")
    print(f"\n  Итого: {ok}/{len(results)}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
