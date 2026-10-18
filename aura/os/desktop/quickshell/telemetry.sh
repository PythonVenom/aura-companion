#!/bin/bash
AURA_STATE=$(jq -r '.state' ~/.cache/aura/aura_status.json 2>/dev/null || echo "offline")
CPU_LOAD=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{printf "%.0f", 100 - $1}')
# Получаем температуру GPU через nvidia-smi (так как у тебя GTX 1070)
GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader 2>/dev/null || echo "N/A")
GPU_LOAD=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null || echo "N/A")

# Выводим в формате JSON
echo "{\"aura\": \"$AURA_STATE\", \"cpu\": \"$CPU_LOAD%\", \"gpu_temp\": \"$GPU_TEMP°C\", \"gpu_load\": \"$GPU_LOAD%\"}"
