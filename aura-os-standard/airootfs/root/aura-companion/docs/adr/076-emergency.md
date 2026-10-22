# ADR-076: Emergency Response

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст

Bug 67 (залипание Aura) под наблюдением, но не закрыт на 100%.
Если Aura залипнет ночью/на встрече — пользователь идёт в терминал kill'ать.
Это трение на каждой итерации.

## Решение

`aura_ctl panic` — композитная команда экстренного останова:
1. `systemctl --user stop aura.service` (graceful)
2. `wpctl set-mute @DEFAULT_SOURCE@ 1` (mic off — гарантия, что не слушает)
3. Лог `~/.cache/aura/panic.log` (timestamp)
4. Notification через notify-send

Также `mute` / `unmute` — отдельные команды для тишины без останова.

## UI

В QML виджете — ряд Emergency (3 кнопки):
- 🆘 PANIC (red, stop + mute)
- 🔇 Mute mic
- 🎙 Unmute

## Последствия

- Одна кнопка = полная безопасность
- Fallback при залипании Bug 67
- Все операции логируются

## Ссылки
- ADR-067 (Widget Control Panel), Bug 67
