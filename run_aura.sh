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

# AURA_AUDIO_WATCHDOG_V1 — проверка audio source при старте
_check_audio() {
    local want="echo-cancel-source"
    local cur=$(pactl get-default-source 2>/dev/null)
    if [ "$cur" != "$want" ]; then
        echo "⚠️  audio source: $cur → переключаю на $want"
        pactl set-default-source "$want" 2>/dev/null || \
            pactl set-default-source "alsa_input.pci-0000_00_1f.3.analog-stereo" 2>/dev/null || true
    fi
    # Проверка что модуль echo-cancel загружен
    if ! pactl list modules short 2>/dev/null | grep -q module-echo-cancel; then
        echo "🎙️ Загружаю module-echo-cancel"
        pactl load-module module-echo-cancel > /dev/null 2>&1 || true
    fi
    # Проверка mute
    local mute=$(pactl get-source-mute "$want" 2>/dev/null | grep -o "yes\|no")
    if [ "$mute" = "yes" ]; then
        echo "🔇 микрофон в mute — снимаю"
        pactl set-source-mute "$want" 0 2>/dev/null || true
    fi
}
_check_audio

# AURA_OLLAMA_WAIT_V1 — ждём ollama API до 30 сек
_wait_ollama() {
    for i in $(seq 1 30); do
        if curl -s -m 1 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
            echo "✅ Ollama готов (через ${i}с)"
            return 0
        fi
        sleep 1
    done
    echo "⚠️ Ollama не отвечает 30с — продолжаю без embeddings"
    return 1
}
_wait_ollama

echo "🦾 Запуск Ауры (модульная архитектура)"
exec python3 aura_main.py
