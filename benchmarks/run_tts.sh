#!/usr/bin/env bash
# TTS: Piper, замер синтеза фразы.
set -e
cd "$(dirname "$0")/.."

PIPER=venv/bin/piper
VOICE=voices/ru_RU-irina-medium.onnx
PHRASE="Аура, который час. Сейчас три часа ночи."
OUT=/tmp/aura_tts_bench.wav

if [ ! -x "$PIPER" ]; then
  echo "Piper не найден: $PIPER"
  exit 1
fi

echo "## TTS (Piper ru_RU-irina-medium)"
echo ""
echo '```'
for i in 1 2 3; do
  START=$(date +%s%N)
  echo "$PHRASE" | "$PIPER" --model "$VOICE" --output_file "$OUT" 2>/dev/null
  END=$(date +%s%N)
  MS=$(( (END - START) / 1000000 ))
  echo "run $i: ${MS} ms"
done
SIZE=$(stat -c %s "$OUT" 2>/dev/null || echo 0)
echo "output: ${SIZE} bytes WAV"
echo '```'
