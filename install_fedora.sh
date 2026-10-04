#!/usr/bin/env bash
# Aura installer для Fedora / RHEL / CentOS
set -euo pipefail

DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true

echo "=== Aura installer (Fedora/RHEL) ==="
echo "Project: $(pwd)"

if ! command -v dnf >/dev/null; then
    echo "dnf не найден. Это не Fedora/RHEL."
    exit 1
fi

PACKAGES=(
    python3.12 python3-pip git
    pipewire pipewire-pulseaudio wireplumber
    pulseaudio-utils playerctl
    vlc ffmpeg portaudio-devel
)
for pkg in "${PACKAGES[@]}"; do
    if $DRY_RUN; then
        echo "[dry-run] dnf install -y $pkg"
    else
        sudo dnf install -y "$pkg" || true
    fi
done

if $DRY_RUN; then
    echo "[dry-run] python3.12 -m venv venv"
else
    python3.12 -m venv venv
    source venv/bin/activate
    pip install -e .
fi

echo "=== Готово ==="
