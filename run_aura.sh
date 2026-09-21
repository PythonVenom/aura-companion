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

# === AEC (PipeWire echo-cancel) для чистого T-one ===
# Гарантируем, что module-echo-cancel загружен и default source = echo-cancel-source.
# Иначе голос Ауры попадает в микрофон (эхо), см. ADR-007.

if command -v pactl > /dev/null 2>&1; then
    if ! pactl list modules short 2>/dev/null | grep -q module-echo-cancel; then
        echo "🎙️ Загружаю module-echo-cancel"
        pactl load-module module-echo-cancel > /dev/null 2>&1 || true
        sleep 2
    fi
    if [ "$(pactl get-default-source 2>/dev/null)" != "echo-cancel-source" ]; then
        echo "🎙️ Устанавливаю default source = echo-cancel-source"
        pactl set-default-source echo-cancel-source > /dev/null 2>&1 || true
    fi
fi

if [ "$AURA_USE_ORCHESTRATOR" = "1" ]; then
    echo "🦾 Запуск в режиме Orchestrator (модульная архитектура)"
    exec python3 aura_main.py
else
    echo "🦾 Запуск в режиме монолита (aura_core.py)"
    exec python3 aura_core.py
fi
