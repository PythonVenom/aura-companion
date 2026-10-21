#!/bin/bash
# Параллельный сбор данных
AURA_STATE=$(jq -r '.state' ~/.cache/aura/aura_status.json 2>/dev/null || echo "offline")
CPU_LOAD=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{printf "%.0f", 100 - $1}')

# Запускаем nvidia-smi в фоне (параллельно)
( nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader > /tmp/gpu_temp.txt 2>/dev/null ) &
( nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits > /tmp/gpu_load.txt 2>/dev/null ) &
wait

GPU_TEMP=$(cat /tmp/gpu_temp.txt || echo "N/A")
GPU_LOAD=$(cat /tmp/gpu_load.txt || echo "N/A")

echo "{\"aura\": \"$AURA_STATE\", \"cpu\": \"$CPU_LOAD%\", \"gpu_temp\": \"$GPU_TEMP°C\", \"gpu_load\": \"$GPU_LOAD%\"}"
