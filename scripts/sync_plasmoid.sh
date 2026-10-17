#!/bin/bash
# Sync плазмоида из git-repo в системную папку Plasma.
# Наука: Idempotent Deploy (Humble/Farley) — можно запускать N раз.
set -e
SRC="$HOME/aura-companion/contrib/plasmoid-aura-status"
DST="$HOME/.local/share/plasma/plasmoids/org.aura.status"
if [ ! -d "$SRC" ]; then
  echo "❌ SRC не найден: $SRC"; exit 1
fi
mkdir -p "$DST"
cp -r "$SRC/contents/"* "$DST/contents/"
cp "$SRC/metadata.json" "$DST/metadata.json"
rm -rf "$DST/__pycache__" 2>/dev/null || true
echo "✅ Sync OK: $SRC → $DST"
ls -la "$DST/contents/ui/"
