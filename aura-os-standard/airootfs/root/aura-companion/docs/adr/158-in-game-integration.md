# ADR-158: Aura внутри игр (in-game integration)

**Статус:** Принято
**Дата:** 2026-10-05

## Контекст

ADR-157 зафиксировал Aura как voice-copilot для разработчиков.
Следующий шаг — **встроить Aura в сами игры** (не только в dev-flow).

Три сценария использования:
1. **Игрок с ограничениями** — голосом управляет персонажем
2. **Elder gamer** — пожилой игрок, голосовые команды вместо кнопок
3. **Обычный игрок** — быстрые команды без отрыва от геймплея
   («Aura, открой инвентарь», «Aura, кто онлайн?»)

## Решение

Три архитектуры интеграции, **последовательно**:

### A. Overlay (v8.2)
- Gamescope overlay (Steam Deck)
- Discord-style overlay на Linux/Windows/macOS
- Перехват голоса → эмуляция ввода
- **Работает без модификации игры**
- Наука: Discord 2015, Gamescope (Valve 2022)

### B. WebSocket bridge (v9.0)
- Игра открывает локальный WS-порт
- Aura подключается: `ws://127.0.0.1:PORT`
- 3 API:
  - `game.state()` → читать состояние (HP, инвентарь)
  - `game.action(cmd)` → игровое действие
  - `game.event(name)` → подписка на события
- **Локально, без облака. GDPR-safe.**
- Наука: Matterbridge-паттерн, WS RFC 6455

### C. Engine plugin (v9.0-v10)
- Unity C# (`AuraSDK.Init()`)
- Unreal C++ (`UAuraSubsystem`)
- Godot GDScript (`Aura.node()`)
- **Требует доступ к коду игры**
- Наука: Unity/Unreal/Godot docs

### Voice → Action (v9.0)
- Steam Input API (Valve 2015)
- Голос → клик/жест/комбинация
- **Особенно важно для accessibility**
- Наука: IGDA 2012, AbleGamers 2004

## In-game scenarios

| Игра | Голос | Зачем |
|---|---|---|
| RPG | «Aura, использовать зелье» | Elder gamer |
| Шутер | «Aura, перезарядись» | Игрок с RSI |
| Стратегия | «Aura, атакуй базу» | Доступность |
| Симулятор | «Aura, проверь статус» | Многозадачность |
| MMO | «Aura, кто онлайн?» | Удобство |

## Технические детали

### Overlay
- Linux: Gamescope API, X11/Wayland overlay
- Windows: DirectX hook, GameBar
- macOS: Metal overlay

### WebSocket bridge
- Игра: 20 строк кода
- Aura: подключается через `os_features.get("game.ws_bridge")`
- Нет модификации игры при overlay-режиме

### Privacy (Nissenbaum 2004)
- Все данные — **локально**
- Никаких облачных аналитик
- Игрок решает, что передавать
- Consent flow (T-sec-4) применяется

## Последствия

### Положительные
- **Новая аудитория**: 3+ млрд геймеров
- **Accessibility для игр** — реальный барьер сейчас
- **Elder gamers** — 25%+ играют
- **Steam Deck native** — Arch + KDE

### Отрицательные
- **Сложность**: 3 архитектуры
- **Производительность**: overlay жрёт ресурсы
- **Безопасность**: WS bridge = потенциальная дыра (mitigate: localhost only)

### Управление
- Elder care — **приоритет №1**
- In-game — **параллельно** (v8.2+)
- Начинаем с Overlay (RICE 120)

## Связанные ADR

- ADR-156 (Plasma symbiosis)
- ADR-157 (Dev copilot)
- ADR-155 (Neuro-rights)

## Ссылки

- Discord Overlay (2015)
- Steam Input API (Valve 2015)
- Gamescope (Valve 2022)
- IGDA Game Accessibility Guidelines (2012)
- AbleGamers Foundation (2004)
- WS RFC 6455 (Fette & Melnikov 2011)
