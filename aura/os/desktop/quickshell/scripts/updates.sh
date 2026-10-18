#!/bin/bash
# Требуется пакет pacman-contrib
UPDATES=$(checkupdates 2>/dev/null | wc -l)
if [ "$UPDATES" -gt 0 ]; then
    echo " $UPDATES обновлений"
else
    echo "✅ Система обновлена"
fi
