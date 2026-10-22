# ADR-017: Platform Abstraction Layer

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

Аура привязана к Linux (PipeWire, systemd, MPRIS). При портировании
на другие ОС придётся переписывать агенты.

## Решение

Выделить Platform Abstraction Layer (PAL) — интерфейсы, которые
агент использует вместо прямых системных вызовов.

### Структура

    aura/platform/
    ├── base.py       Protocol-интерфейсы
    ├── linux.py      PipeWire + systemd + MPRIS
    ├── ubuntu.py     PipeWire/PulseAudio fallback
    ├── windows.py    WASAPI + WinAPI
    ├── macos.py      CoreAudio + AppleScript
    └── __init__.py   автовыбор по sys.platform + /etc/os-release

### Интерфейсы

**AudioDevice:**
- list_sinks, list_sources
- get_default_sink, set_default_sink
- duck, unduck

**SystemService:**
- enable_autostart, disable_autostart
- notify

**MediaController:**
- list_players
- pause_all, resume_all
- get_last_active

### Использование

    from aura.platform import get_audio
    get_audio().duck(0.2)

Агенты не знают про ОС — используют PAL.

## Последствия

**Плюсы:**
- Один код — разные платформы
- Тестируемость (mock PAL)
- Изоляция платформенных багов

**Минусы:**
- Дополнительный слой абстракции
- Первые 2 недели — рефакторинг

## Связанные

- ADR-004 (dead code)
- ADR-011 (modular architecture)
- ADR-016 (Plasma Architecture)
- ADR-022 (cross-platform strategy)
