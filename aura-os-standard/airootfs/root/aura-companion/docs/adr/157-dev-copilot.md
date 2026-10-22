# ADR-157: Aura как voice-copilot для разработчиков

**Статус:** Принято
**Дата:** 2026-10-05

## Контекст

Aura создавалась для elder care. Но её ядро (49 агентов, HAL, os_features)
применимо **не только для пожилых**. Разработчики игр и ПО тоже страдают:

- Много рутины: коммиты, тесты, логи, поиск в доках
- Accessibility-проблемы: RSI, ограничения моторики
- Voice-first интерфейс помогает **любому** разработчику

Steam Deck (Arch + KDE) — **прямая база для Aura**. Steamworks SDK —
**канал дистрибуции** для gamedev-инструмента.

## Решение

Aura становится **voice-copilot для разработчиков** — параллельно с elder care.
Один движок. Два профиля:

1. **Aura for Elder** (текущий) — простой UI, 3 кнопки
2. **Aura for Devs** — CLI + IDE bridge + CI/CD

### Что даёт разработчику

- **Bug logging голосом**: «Aura, баг: кнопка X не работает»
- **Code review**: «Aura, что делает функция parse_args?»
- **Commit**: «Aura, закоммить: fix input lag»
- **Docs search**: «Aura, найди в Steamworks: achievements API»
- **Build**: «Aura, собери Windows + Linux build»
- **Playtest**: Aura эмулирует клики/жесты по голосу

### SDK (T-steam-6)

    pip install aura-steam-sdk

3 API:
- `input` — voice → game action (Steam Input bridge)
- `telemetry` — игровая аналитика (локально, GDPR-safe)
- `achievements` — достижения через голос

### CLI (T-dev-2)

    aura dev build           # сборка
    aura dev test            # тесты
    aura dev commit "msg"    # git commit
    aura dev log-bug "..."   # запись бага
    aura dev deploy          # CI/CD

## Наука

- Brooks 1975 (Mythical Man-Month) — productivity critical
- Nielsen 1993 — usability для разработчиков
- Licklider 1960 — man-computer symbiosis
- IGDA Game Accessibility 2012
- AbleGamers 2004
- Steamworks SDK (Valve)

## Последствия

### Положительные
- **Новая аудитория**: разработчики → 27+ млн на Steam
- **Дистрибуция через Steam**: Workshop, Store
- **Steam Deck native**: Arch + KDE (уже наша база)
- **Accessibility для геймеров** (новая вертикаль)
- **Aura становится инструментом**, не только приложением

### Отрицательные
- **Раздвоение фокуса**: elder care vs devs
- **Больше тестирования**: 2 профиля
- **Steamworks SDK** — тяжёлая зависимость

### Управление
- Elder care — **приоритет №1** (v8.0)
- Dev tooling — **параллельно** (v8.2+), не вместо

## Связанные ADR

- ADR-156 (Plasma symbiosis)
- ADR-017 (Platform abstraction)
- ADR-044 (Founder-first beachhead)

## Ссылки

- Brooks F. (1975). The Mythical Man-Month.
- Nielsen J. (1993). Usability Engineering.
- Licklider J.C.R. (1960). Man-Computer Symbiosis.
- IGDA (2012). Game Accessibility Guidelines.
- Valve (2022). SteamOS 3.0 Documentation.
