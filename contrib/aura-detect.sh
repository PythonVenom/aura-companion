#!/usr/bin/env bash
# aura-detect.sh — определение железа для профиля installer
# Вывод: shell-переменные AURA_PROFILE, AURA_RAM_GB, AURA_CPU_CORES, AURA_GPU

detect_ram() {
    if [ -f /proc/meminfo ]; then
        awk '/MemTotal/ {print int($2 / 1024 / 1024)}' /proc/meminfo
    else
        # macOS
        sysctl -n hw.memsize 2>/dev/null | awk '{print int($1 / 1024 / 1024 / 1024)}'
    fi
}

detect_cores() {
    nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2
}

detect_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        nvidia-smi -L 2>/dev/null | head -1 && return 0
    fi
    if command -v lspci >/dev/null 2>&1; then
        lspci 2>/dev/null | grep -iE "vga|3d" | head -1
    fi
    echo "no-gpu"
}

detect_profile() {
    local ram=$1
    # cores зарезервировано на будущее
    if [ "$ram" -le 4 ]; then echo "minimal"
    elif [ "$ram" -le 8 ]; then echo "low"
    elif [ "$ram" -le 16 ]; then echo "medium"
    else echo "full"
    fi
}

AURA_RAM_GB=$(detect_ram)
AURA_CPU_CORES=$(detect_cores)
AURA_GPU=$(detect_gpu)
AURA_PROFILE=$(detect_profile "$AURA_RAM_GB")

export AURA_RAM_GB AURA_CPU_CORES AURA_GPU AURA_PROFILE

if [ "${AURA_DETECT_VERBOSE:-0}" = "1" ]; then
    echo "RAM:      ${AURA_RAM_GB} GB"
    echo "CPU:      ${AURA_CPU_CORES} cores"
    echo "GPU:      ${AURA_GPU}"
    echo "PROFILE:  ${AURA_PROFILE}"
fi
