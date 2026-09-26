#!/bin/bash
# Aura launcher — модульная архитектура.
#
# Запускает aura_main.py.
# Монолит выведен в attic/ (ADR-008, тег legacy-monolith-final).
# Откат: git checkout legacy-monolith-final.

# Ждём XAUTHORITY
while [ -z "$XAUTHORITY" ] || [ ! -f "$XAUTHORITY" ]; do
    export XAUTHORITY=$(ls /tmp/xauth_* 2>/dev/null | head -1)
    [ -n "$XAUTHORITY" ] && break
    sleep 1
done

export DISPLAY=:0

# PROJECT_DIR — путь к проекту (не хардкод).
# Работает при запуске из любого места: bash run_aura.sh,
# /полный/путь/run_aura.sh, через systemd.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
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
fi

echo "🦾 Запуск Ауры (модульная архитектура)"
exec python3 aura_main.py
