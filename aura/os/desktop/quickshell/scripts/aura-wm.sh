#!/bin/bash
# Адаптер управления окнами (X11 vs Wayland)

ACTION=$1
SESSION_TYPE=$(echo $XDG_SESSION_TYPE | tr '[:upper:]' '[:lower:]')

if [ "$SESSION_TYPE" == "wayland" ]; then
    # В БУДУЩЕМ: Здесь будет логика для Hyprland / Niri
    case "$ACTION" in
        overview) echo "Wayland: Обзор окон пока не настроен" ;;
        next_ws) echo "Wayland: Переключение воркспейсов (hyprctl dispatch workspace e+1)" ;;
        prev_ws) echo "Wayland: Переключение воркспейсов (hyprctl dispatch workspace e-1)" ;;
    esac
else
    # СЕЙЧАС: Логика для X11 (Openbox)
    case "$ACTION" in
        overview) skippy-xd --expose ;; # Вызов Expose
        next_ws) wmctrl -s $(( ($(wmctrl -d | grep '\*' | awk '{print $1}') + 1) % $(wmctrl -d | wc -l) )) ;;
        prev_ws) wmctrl -s $(( ($(wmctrl -d | grep '\*' | awk '{print $1}') - 1 + $(wmctrl -d | wc -l)) % $(wmctrl -d | wc -l) )) ;;
    esac
fi
