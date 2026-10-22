#!/usr/bin/env bash
# Aura installer для macOS
set -euo pipefail

DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true

echo "=== Aura installer (macOS) ==="
echo "Project: $(pwd)"
echo "Dry-run: $DRY_RUN"

if ! command -v brew >/dev/null; then
    echo "❌ Homebrew не найден: https://brew.sh"
    exit 1
fi

PACKAGES=(python@3.12 git ffmpeg portaudio)
for pkg in "${PACKAGES[@]}"; do
    if $DRY_RUN; then
        echo "[dry-run] brew install $pkg"
    else
        brew install "$pkg" || true
    fi
done

if $DRY_RUN; then
    echo "[dry-run] python3 -m venv venv"
    echo "[dry-run] pip install -e ."
else
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
fi

echo ""
echo "=== Готово ==="
echo "Запусти: source venv/bin/activate && python -m aura_main"
