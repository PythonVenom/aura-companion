#!/usr/bin/env bash
# 24-часовой прогон стабильности Aura (ADR-010 beta).
# Пишет метрики в /tmp/aura_stability.log и CSV.
set -euo pipefail

DURATION_H="${1:-24}"
OUT="${2:-/tmp/aura_stability}"
INTERVAL=60

mkdir -p "$OUT"
CSV="$OUT/metrics.csv"
LOG="$OUT/run.log"

echo "start_ts,duration_h,service,rss_mb,cpu_pct,errors_5min,restarts" > "$CSV"
echo "[$(date -Iseconds)] Старт прогона: ${DURATION_H}ч, интервал ${INTERVAL}с" | tee -a "$LOG"

END=$(( $(date +%s) + DURATION_H * 3600 ))
ITER=0

while [ "$(date +%s)" -lt "$END" ]; do
    ITER=$((ITER + 1))
    TS=$(date -Iseconds)

    # Статус сервиса
    SERVICE=$(systemctl --user is-active aura.service 2>/dev/null || echo "inactive")

    # RSS процесса
    RSS_MB=$(ps -o rss= -C python3 2>/dev/null | awk '{s+=$1} END {print int(s/1024)}' || echo 0)

    # CPU
    CPU_PCT=$(ps -o %cpu= -C python3 2>/dev/null | awk '{s+=$1} END {printf "%.1f", s}' || echo 0)

    # Ошибки за 5 мин
    ERRORS=$(journalctl --user -u aura.service --since "5 min ago" 2>/dev/null | grep -ci "error\|exception\|traceback" || echo 0)

    # Рестарты
    RESTARTS=$(systemctl --user show aura.service -p NRestarts --value 2>/dev/null || echo 0)

    echo "$TS,$DURATION_H,$SERVICE,$RSS_MB,$CPU_PCT,$ERRORS,$RESTARTS" >> "$CSV"
    echo "[$TS] #$ITER service=$SERVICE rss=${RSS_MB}M cpu=${CPU_PCT}% err5m=$ERRORS restarts=$RESTARTS" | tee -a "$LOG"

    sleep "$INTERVAL"
done

echo "[$(date -Iseconds)] Прогон завершён. CSV: $CSV" | tee -a "$LOG"
