#!/bin/bash
# Установка плазмоида через kpackagetool6.
set -e
SRC="$HOME/aura-companion/contrib/plasmoid-aura-status"
DST="$HOME/.local/share/plasma/plasmoids/org.aura.status"

if kpackagetool6 --type Plasma/Applet --list 2>/dev/null | grep -q "^org.aura.status$"; then
  echo "🔄 Уже установлен — обновляем"
  kpackagetool6 --type Plasma/Applet --upgrade "$SRC"
else
  echo "➕ Установка впервые"
  kpackagetool6 --type Plasma/Applet --install "$SRC"
fi

echo "=== VERIFY ==="
kpackagetool6 --type Plasma/Applet --list 2>/dev/null | grep aura
ls -la "$DST/contents/ui/main.qml"
