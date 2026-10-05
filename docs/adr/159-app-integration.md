# ADR-159: Aura внутри приложений (app integration)

**Статус:** Принято
**Дата:** 2026-10-05

## Контекст

ADR-156 — симбиоз с ОС. ADR-157 — voice-copilot для разработчиков.
ADR-158 — внутри игр. Следующий уровень: **внутри творческих,
научных и профессиональных приложений.**

Blender, Reaper, Cubase, Minecraft, Jupyter, ELN — у всех есть
**plugin API**. Aura может стать **голосовым слоем** внутри них.

## Решение

Aura интегрируется через **plugin API каждого приложения**.
Не заменяет — **дополняет**. Один движок, много хостов.

### Целевые приложения

| Приложение | Plugin API | Аудитория |
|---|---|---|
| Blender | bpy (Python) | 3D-художники, геймдев |
| Reaper | ReaScript (Lua/EEL/Python) | Музыканты, звукорежи |
| Cubase | VST3 / AKI | Профи-студии |
| Minecraft | Forge / Fabric (Java) | Дети, elder gamers |
| Jupyter | Kernel API (Python) | Учёные, data scientists |
| ELN | RFC 2020 | Лаборатории |
| VS Code / JetBrains | LSP / Extension API | Разработчики |

### Общий framework (T-app-7)

    # aura/app_integration/base.py
    class AuraPlugin:
        def __init__(self, host: str): ...
        def register(self, command: str, handler): ...
        def on_voice(self, text: str) -> bool: ...

    # Пример: Blender
    plugin = AuraPlugin("blender")
    plugin.register("добавь куб", lambda: bpy.ops.mesh.primitive_cube_add())

### Сценарии

**Blender** — «Aura, добавь куб», «Aura, рендер 4K», «Aura, выдели всё».
**Reaper** — «Aura, нормализуй трек», «Aura, экспорт MP3».
**Cubase** — «Aura, добавь компрессор», «Aura, квантайз».
**Minecraft** — «Aura, поставь блок», «Aura, телепорт».
**Jupyter** — «Aura, запусти ячейку», «Aura, построй график».
**ELN** — «Aura, запиши pH 7.2», «Aura, найди протокол».

## Для кого

1. **Профессионалы** — быстрее, без отрыва от работы
2. **Accessibility** — RSI, моторика, зрение
3. **Elder users** — пожилые творцы, учёные
4. **Дети** — Minecraft без клавиатуры

## Наука

- Gamma et al. 1994 — Plugin / Strategy pattern
- Licklider 1960 — Man-Computer Symbiosis
- Nielsen 1993 — Usability для профи
- Blender Python API (2023)
- ReaScript (Cockos 2006)
- VST3 (Steinberg 2011)
- Minecraft Forge (2011)
- Jupyter Kernel (2014)
- ELN RFC (2020)

## Приватность

- Всё **локально**. Никаких облачных аналитик.
- Consent flow (T-sec-4) применяется.
- Игрок/учёный решает, что передавать.

## Последствия

### Положительные
- **Новая аудитория**: 100+ млн творческих + научных пользователей
- **Accessibility для профи** — реальная ниша
- **Blender/Reaper/Jupyter** — open source, легче интегрировать
- **Elder artists/scientists** — пожилые творцы

### Отрицательные
- **Много адаптеров** (8+ plugin API)
- **Тестирование** каждого отдельно
- **Зависимость** от версии приложения

### Управление
- Elder care — приоритет №1
- App-integration — параллельно (v8.2+)
- Начинаем с Jupyter + VS Code (RICE 120-125)

## Связанные ADR

- ADR-156 (Plasma — OS)
- ADR-157 (Dev copilot)
- ADR-158 (In-game)
- ADR-155 (Neuro-rights)

## Ссылки

- Blender Python API (docs.blender.org, 2023)
- ReaScript (reaper.fm, Cockos 2006)
- VST3 (Steinberg 2011)
- Minecraft Forge (2011)
- Jupyter Kernel (jupyter.org, 2014)
- Licklider J.C.R. (1960). Man-Computer Symbiosis.
