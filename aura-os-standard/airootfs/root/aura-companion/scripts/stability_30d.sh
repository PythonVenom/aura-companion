#!/bin/bash
# 30-day stability test (F-026)
# Наука: Boehm 1981 (40-60% времени — maintenance).
# Каждые 10 минут: pytest + health check + логи.
# Запуск: nohup ./stability_30d.sh > /tmp/aura_30d.log 2>&1 &

DURATION_DAYS=30
INTERVAL_SEC=600   # 10 минут
LOG=/tmp/aura_stability_$(date +%Y%m%d).log
STATE=/tmp/aura_stability_state.json

echo "{\"start\": $(date +%s), \"cycles\": 0, \"failures\": 0}" > "$STATE"

cycle=0
while true; do
    cycle=$((cycle+1))
    ts=$(date -Iseconds)
    echo "[$ts] cycle $cycle" >> "$LOG"

    # 1. Aura жива?
    if pgrep -f aura_main.py > /dev/null; then
        echo "  ✅ aura_main running" >> "$LOG"
    else
        echo "  ❌ aura_main DEAD" >> "$LOG"
    fi

    # 2. Трей живой?
    if pgrep -f aura_tray > /dev/null; then
        echo "  ✅ tray running" >> "$LOG"
    fi

    # 3. SQLCipher OK?
    if python3 -c "import sqlcipher3" 2>/dev/null; then
        echo "  ✅ sqlcipher" >> "$LOG"
    fi

    # 4. Rapid smoke (60 сек)
    if cd /home/pythonvenom/aura_project && \
       source venv/bin/activate && \
       timeout 60 pytest tests/test_consent.py tests/test_capability_integration.py -q --tb=line > /dev/null 2>&1; then
        echo "  ✅ pytest smoke" >> "$LOG"
    else
        echo "  ❌ pytest FAILED" >> "$LOG"
    fi

    # Update state
    python3 << PYEOF
import json, time
with open("$STATE") as f: s = json.load(f)
s["cycles"] = $cycle
s["last"] = time.time()
with open("$STATE", "w") as f: json.dump(s, f)
PYEOF

    # Статистика
    if [ $((cycle % 144)) -eq 0 ]; then
        echo "[$ts] 📊 DAY $((cycle / 144)) полный" >> "$LOG"
    fi

    sleep $INTERVAL_SEC
done
