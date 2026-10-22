# ADR-037: Third-party API Wrappers

**Дата:** 2026-09-28
**Статус:** Проект
**Связано:** ADR-036 (Creative & Craftsman)

## Контекст

Aura Craft требует интеграций с 20+ профессиональными приложениями:
Blender, Photoshop, Figma, Ableton, AutoCAD, SolidWorks, LinuxCNC, Lightroom.

**Прямое встраивание — плохо:**
- Разные языки (Python, C++, JS, Lua)
- Разные API (COM, REST, OSC, serial)
- Разные версии (Blender 3.x vs 4.x)

## Решение

**Слой Wrappers** — единый интерфейс для сторонних приложений.

### Архитектура

    AuraAgent → AppWrapper (interface) → Adapter → App API

### Интерфейс AppWrapper

    class AppWrapper:
        name: str                    # "blender", "figma"
        version: str                 # "4.2+"
        def is_available(self) -> bool
        def connect(self) -> bool
        def execute(self, cmd: str, params: dict) -> dict
        def disconnect(self) -> None

### Реализации (по приоритету)

| App | Транспорт | Стек | Приоритет |
|---|---|---|---|
| Blender | Python API (bpy) | subprocess + TCP | **P1** |
| Figma | REST + Plugin | HTTPS + WebSocket | **P1** |
| Photoshop | COM (Windows) / scripting | pywin32 / ExtendScript | **P2** |
| Krita | Python API | PyKrita + TCP | **P2** |
| Ableton | OSC | python-osc | **P2** |
| Reaper | ReaScript | Lua + OSC | **P2** |
| FL Studio | MIDI | mido + portmidi | **P3** |
| DaVinci Resolve | Python API | DaVinci Resolve Scripting | **P2** |
| Lightroom | Lua SDK | subprocess | **P3** |
| AutoCAD | COM / Python | pyautocad | **P3** |
| Fusion 360 | Python API | REST + websocket | **P2** |
| SolidWorks | COM | pywin32 | **P3** |
| LinuxCNC | gRPC / serial | grpcio | **P1** |
| GRBL | Serial | pyserial | **P1** |
| OctoPrint | REST | aiohttp | **P2** |
| PrusaSlicer | CLI | subprocess | **P3** |
| Blender-CV | OpenCV | cv2 | **P3** |

### Discovery

- **Auto-detect:** check for binary / socket / D-Bus name
- **Config:** `~/.config/aura/wrappers.json` — override
- **Fallback:** keyboard/mouse emulation (xdotool/ydotool) если API нет

### Безопасность

- **Whitelist команд** — wrapper знает, что можно
- **Sandbox** — subprocess с ограничениями
- **Confirm для destructive:** удаление объектов, отправка на печать, старт станка

### Что НЕ делаем

- Универсальный "AI оператор UI" через CV (нестабильно, YAGNI)
- Прямое управление ЧПУ без safety-чека (производственная безопасность)

## Последствия

**Плюсы:** единый интерфейс, легко добавить новый App
**Минусы:** 17 wrappers × разный код = много работы
**Roadmap:** 1 wrapper / 2 недели, Q2-Q4 2026

## Связанные
- ADR-036 (Creative & Craftsman)
- ADR-030 (Developer Mode)
