# ADR-081: SNI Tray (pystray)

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст

Aura работает в Plasma (widget). Нужен трей для остальных DE:
GNOME, Cinnamon, XFCE, MATE, LXQt, Budgie, i3, Sway, Hyprland.

StatusNotifierItem (SNI) — стандарт D-Bus, покрывает ~90% Linux DE.

## Решение

`aura/core/tray.py` — TrayIcon на pystray.
- Иконка = кружок с цветом статуса
- Меню: Статус, Pause/Resume, Web UI, Kill, Quit
- Действия через `aura_ctl.py` (subprocess)
- Web UI открывается через `xdg-open /ui`
- Полл /status каждые N сек (позже — push через WebSocket)

Совместимость:
- KDE Plasma: нативная ✓
- GNOME: с расширением `appindicator-support` ✓
- Cinnamon: нативная ✓
- XFCE: с `xfce4-statusnotifier-plugin` ✓
- MATE: с `indicator-applet` ✓
- LXQt: нативная ✓
- Budgie: нативная ✓
- i3/Sway/Hyprland: через waybar/polybar ✓

## YAGNI

- Не пишем свой SNI D-Bus клиент (pystray делает)
- Не делаем отдельную иконку на каждое DE (один SNI)
- Не пишем GUI (Web UI есть)

## Последствия

- 90% DE покрыто одной библиотекой
- Ставится отдельно от Aura (aura_tray.service) — опционально
- Windows/macOS тоже работают через pystray

## Ссылки
ADR-079 (HTTP API), ADR-080 (Web UI), ADR-067 (Plasma widget)
