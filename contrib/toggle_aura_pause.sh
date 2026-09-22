#!/usr/bin/env bash
# Toggle паузы Ауры. См. Фаза 9.3.1.
# Привязать в KDE: System Settings → Shortcuts → Custom Shortcuts.
FLAG=/tmp/aura_pause.flag
if [ -f "$FLAG" ]; then
    rm -f "$FLAG"
    notify-send -i audio-input-microphone "Аура" "▶ Слушает" 2>/dev/null || true
else
    touch "$FLAG"
    notify-send -i media-playback-pause "Аура" "⏸ На паузе" 2>/dev/null || true
fi
