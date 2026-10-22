#!/bin/bash
# build_iso.sh — сборка Aura Live-USB
set -e
PROFILE="$HOME/aura_project/platforms/archiso"
WORK="$HOME/aura_project/platforms/work"
OUT="$HOME/aura_project/platforms/out"

echo "=== Aura ISO build ==="
if ! command -v mkarchiso &>/dev/null; then
    echo "❌ mkarchiso не найден (sudo pacman -S archiso)"
    exit 1
fi
if [ ! -d "$PROFILE" ]; then
    echo "❌ Профиль не найден: $PROFILE"
    exit 1
fi
sudo mkarchiso -v -w "$WORK" -o "$OUT" "$PROFILE"
echo ""
echo "✅ ISO создан: $OUT"
ls -lh "$OUT/"*.iso 2>/dev/null || true
