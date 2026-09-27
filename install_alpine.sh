#!/usr/bin/env sh
# Aura installer для Alpine Linux
set -eu

echo "=== Aura installer (Alpine) ==="
echo "Project: $(pwd)"

if ! command -v apk >/dev/null; then
    echo "apk не найден. Это не Alpine."
    exit 1
fi

apk add --no-cache \
    python3 py3-pip git \
    pipewire pipewire-pulse wireplumber \
    pulseaudio-utils playerctl vlc ffmpeg \
    py3-virtualenv py3-numpy

python3 -m venv venv
. venv/bin/activate
pip install -e .

echo "=== Готово ==="
