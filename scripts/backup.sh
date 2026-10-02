#!/usr/bin/env bash
# Backup ~/.cache/aura + ~/.config/aura в tar.gz
set -e
TS=$(date +%Y%m%d-%H%M%S)
OUT="$HOME/aura_backups/aura-$TS.tar.gz"
mkdir -p "$HOME/aura_backups"
tar czf "$OUT" \
    -C "$HOME" \
    .cache/aura \
    .config/aura \
    --exclude='*.sock' \
    --exclude='*.log' 2>/dev/null || true
echo "[ok] $OUT ($(du -h "$OUT" | cut -f1))"
ls -lt "$HOME/aura_backups" | head -5
