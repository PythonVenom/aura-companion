#!/usr/bin/env bash
# restore.sh <backup.tar.gz>
set -e
ARCHIVE="${1:?usage: restore.sh <backup.tar.gz>}"
[ -f "$ARCHIVE" ] || { echo "❌ нет файла $ARCHIVE"; exit 1; }
read -p "Перезапишет ~/.cache/aura и ~/.config/aura. Продолжить? [y/N] " ok
[ "$ok" = "y" ] || { echo "отменено"; exit 0; }
tar xzf "$ARCHIVE" -C "$HOME"
echo "[ok] восстановлено из $ARCHIVE"
