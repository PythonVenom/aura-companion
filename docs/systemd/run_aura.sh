#!/bin/bash
# Aura launcher — с флагом переключения на модульную архитектуру.
#
# По умолчанию — старый монолит (aura_core.py). Работает, проверено.
# С AURA_USE_ORCHESTRATOR=1 — новый модульный роутинг (aura_main.py).
#
# Откат: убрать переменную из systemd-юнита или отсюда.

# Ждём XAUTHORITY
while [ -z "$XAUTHORITY" ] || [ ! -f "$XAUTHORITY" ]; do
    export XAUTHORITY=$(ls /tmp/xauth_* 2>/dev/null | head -1)
    [ -n "$XAUTHORITY" ] && break
    sleep 1
done

export DISPLAY=:0
cd /home/pythonvenom/aura_project
source venv/bin/activate

if [ "$AURA_USE_ORCHESTRATOR" = "1" ]; then
    echo "🦾 Запуск в режиме Orchestrator (модульная архитектура)"
    exec python3 aura_main.py
else
    echo "🦾 Запуск в режиме монолита (aura_core.py)"
    exec python3 aura_core.py
fi
