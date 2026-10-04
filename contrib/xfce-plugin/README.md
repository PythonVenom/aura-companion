# Aura XFCE Panel Plugin (genmon)

XFCE panel plugin через `xfce4-genmon-plugin`.

## Установка

1. Установить: `sudo pacman -S xfce4-genmon-plugin` (или apt/dnf)
2. Правый клик на панели → Panel → Add New Items → Generic Monitor
3. Настроить команду:
   `python3 ~/aura_project/contrib/xfce-plugin/aura-xfce.py`
4. Период обновления: 2 секунды

## Как работает

Скрипт выводит в stdout формат genmon:
- `<txt>...</txt>` — текст
- `<tool>...</tool>` — tooltip
- `<click>...</click>` — команда на клик
