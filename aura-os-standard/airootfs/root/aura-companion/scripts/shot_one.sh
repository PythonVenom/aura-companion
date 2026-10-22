#!/usr/bin/env bash
# Запись одного видео БЕЗ сценария. Использование: shot_one.sh <name> [duration]
set -euo pipefail
NAME="${1:-aura_demo}"
DUR="${2:-90}"
OUT="$HOME/${NAME}_$(date +%H%M%S).mp4"

MONITOR=$(pactl list short sources | awk '/monitor/ {print $2; exit}')
echo "📹 $NAME ${DUR}с → $OUT"
echo "monitor: ${MONITOR:-none}"
sleep 3

if [ -n "$MONITOR" ]; then
    ffmpeg -y -f x11grab -framerate 30 -video_size 1920x1080 -i :0.0 \
      -f pulse -i default -f pulse -i "$MONITOR" \
      -filter_complex "[1:a][2:a]amix=inputs=2:duration=longest[aout]" \
      -map 0:v -map "[aout]" \
      -c:v libx264 -preset ultrafast -crf 28 \
      -c:a aac -b:a 128k -t "$DUR" "$OUT" &
else
    ffmpeg -y -f x11grab -framerate 30 -video_size 1920x1080 -i :0.0 \
      -f pulse -i default \
      -c:v libx264 -preset ultrafast -crf 28 \
      -c:a aac -b:a 128k -t "$DUR" "$OUT" &
fi

FFMPEG_PID=$!
echo "🎬 ИДЁТ. Говори в комнату."
wait $FFMPEG_PID || true
ls -lh "$OUT"
echo "Готово: $OUT"
