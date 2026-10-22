#!/usr/bin/env bash
# Aura installer для Ubuntu/Debian
set -euo pipefail

DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true

echo "=== Aura installer (Ubuntu/Debian) ==="
echo "Project: $(pwd)"

if ! command -v apt >/dev/null; then
    echo "apt не найден. Это не Ubuntu/Debian."
    exit 1
fi

PACKAGES=(
    python3.12 python3.12-venv python3-pip
    pipewire pipewire-pulse pipewire-audio wireplumber
    pulseaudio-utils playerctl vlc ffmpeg
    portaudio19-dev libsndfile1 git curl
)
for pkg in "${PACKAGES[@]}"; do
    if $DRY_RUN; then
        echo "[dry-run] apt install -y $pkg"
    else
        sudo apt install -y "$pkg" || true
    fi
done

if $DRY_RUN; then
    echo "[dry-run] python3 -m venv venv"
else
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
fi

echo "=== Готово ==="
