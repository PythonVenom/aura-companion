#!/usr/bin/env bash
cd "$HOME/aura_project"
source venv/bin/activate

pkill -9 -f aura_main 2>/dev/null
pkill -9 -f aura_diag 2>/dev/null
sleep 1
rm -f /tmp/aura_diag.log /tmp/aura_diag_extra.log

python3 tools/aura_diag.py >/dev/null 2>&1 &
WRAP=$!
echo "diag pid=$WRAP"
echo
echo "1) Скажи голосом: 'Аура, сколько времени'"
echo "2) Дождись зависания (жёлтый индикатор, тишина)"
echo "3) Через ~10 сек нажми Enter здесь"
read -r

kill -USR1 "$WRAP" 2>/dev/null
sleep 1

{
  echo "=== /proc/$WRAP/wchan ==="
  cat /proc/$WRAP/wchan 2>/dev/null; echo
  echo "=== /proc/$WRAP/status ==="
  grep -E '^(Name|State|Threads|VmRSS)' /proc/$WRAP/status 2>/dev/null
  echo "=== per-thread wchan ==="
  for t in /proc/$WRAP/task/*; do
    echo "tid=$(basename "$t") wchan=$(cat "$t/wchan" 2>/dev/null)"
  done
  echo "=== py-spy (best effort) ==="
  py-spy dump --pid "$WRAP" 2>&1 | head -80 || echo "py-spy failed"
  echo "=== gdb (best effort, needs sudo -n) ==="
  sudo -n gdb -p "$WRAP" -batch -ex "thread apply all bt" 2>&1 | head -120 || echo "gdb skipped"
} | tee /tmp/aura_diag_extra.log

kill -9 "$WRAP" 2>/dev/null

echo
echo "===== /tmp/aura_diag.log ====="
cat /tmp/aura_diag.log
echo
echo "===== /tmp/aura_diag_extra.log ====="
cat /tmp/aura_diag_extra.log
