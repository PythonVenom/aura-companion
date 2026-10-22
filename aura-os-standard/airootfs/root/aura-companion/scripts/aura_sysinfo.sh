#!/bin/bash
# Aura sysinfo — JSON для плазмоида. Адаптер над /proc, free, sensors.
set -e
CPU_LOAD=$(cut -d' ' -f1 /proc/loadavg)
CPU_CORES=$(nproc)
RAM_USED=$(free -m | awk '/^Mem:/ {print $3}')
RAM_TOTAL=$(free -m | awk '/^Mem:/ {print $2}')
CPU_TEMP=$(sensors 2>/dev/null | grep -m1 'Package id 0' | awk '{print $4}' | tr -d '+°C' || echo "?")
printf '{"cpu_load":"%s","cpu_cores":%s,"ram_used":%s,"ram_total":%s,"cpu_temp":"%s"}\n' \
  "$CPU_LOAD" "$CPU_CORES" "$RAM_USED" "$RAM_TOTAL" "$CPU_TEMP"
