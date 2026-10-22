#!/usr/bin/env bash
# Запись demo-видео Aura через ffmpeg (X11 + Pulse).
# Использование: scripts/demo_record.sh [output.mp4] [duration_sec]
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="${1:-$HOME/aura_demo.mp4}"
DUR="${2:-90}"

echo "Запись ${DUR}с → $OUT"
echo "Через 3 сек начнётся запись..."
sleep 3

ffmpeg -y -f x11grab -framerate 30 -video_size 1920x1080 -i :0.0 \
  -f pulse -i default \
  -c:v libx264 -preset ultrafast -crf 28 \
  -c:a aac -b:a 128k \
  -t "$DUR" "$OUT" &
FFMPEG_PID=$!

bash scripts/demo_scenario.sh
wait $FFMPEG_PID || true

ls -lh "$OUT"
echo "Готово: $OUT"
