# ADR-062: Dragon Core (визуальный слой)

**Дата:** 2026-10-02
**Статус:** Проект

## Контекст

Aura — голосовой слой над ОС. Пользователь хочет видеть её состояние
не только через виджет-иконку, но и через **живой визуальный слой** на
рабочем столе: дыхание при idle, волна при listening, спектр при speaking.

Аналог: MSI Dragon Core, «Универсальный солдат» (визуализация сущности),
но в стиле Aura — неон, бирюза, техно-минимализм.

## Решение (черновик)

Полноэкранный QML визуализатор на рабочем столе (KDE Plasma 6, Wayland):
- Прозрачное окно, без рамок, на весь экран
- KWin Rules: Keep Below + Click Through (как обои)
- Стек: QML + cava (FFT) + FIFO + DBus
- Машина состояний: IDLE / LISTENING / THINKING / SPEAKING / ERROR

Три слоя:
    QML Renderer (визуализация)
       ↓
    Audio FFT (cava + FIFO)
       ↓
    State Stream (DBus StateChanged от aura_main)

## YAGNI

MVP = прозрачное окно + простой пульсирующий круг по FFT.
Дракон/шейдеры/particles — итерации 2–3.

## ToC

Узкое место — визуализация **должна работать на 60 FPS** без блокировки Aura.
Решение: изолированный процесс, отдельный от aura.service.

## Открытые вопросы

1. cava → FIFO → QML: точный формат JSON
2. Click Through на Wayland: KWin Rules работают стабильно?
3. Пресеты: low/medium/high для разного железа
4. Песочница настроек (UI)

## Последствия

- Новый процесс `aura-dragon.service` (user systemd)
- Отдельный plasmoid `org.aura.dragon`
- Не блокирует основную Aura

## Ссылки
- ADR-062 (в VISION-2026-09-30)
- ADR-067 (Widget Control Panel)
