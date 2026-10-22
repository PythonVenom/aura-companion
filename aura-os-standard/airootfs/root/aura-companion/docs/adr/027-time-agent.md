# ADR-027: TimeAgent

**Дата:** 2026-09-28
**Статус:** Принято

## Контекст

Массажисту — таймер сессии. Маме — будильник утром. Школьнику — Pomodoro.

## Решение

**TimeAgent** — таймеры, будильники. State в `/tmp/aura_timers.json`.

### API

- `add_timer(seconds, label)` — таймер
- `add_alarm(hour, minute)` — будильник
- `list_pending()` — активные
- `get_fired()` — сработавшие

### Команды

- «Аура, таймер 5 минут»
- «Аура, разбуди в 7:30»
- «Аура, какие таймеры»

### Почему не time.sleep

- Переживёт рестарт (state JSON)
- Не держит Python-процесс
- Позже: systemd-timer

### Proactive

`ProactiveEngine` проверяет `get_fired()` каждые 30 сек.

## Связанные

- ADR-014 (Proactive)
- ADR-013 (Dialogue Manager)
