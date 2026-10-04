#!/usr/bin/env bash
# Копирует скриншот в docs/screenshots/ с именем для README.
# Usage: ./scripts/publish_screenshot.sh <path> <public-name.png>
set -e
SRC="$1"
NAME="$2"
if [ -z "$SRC" ] || [ -z "$NAME" ]; then
  echo "Usage: $0 <source-path> <public-name.png>"
  exit 1
fi
[ ! -f "$SRC" ] && echo "Not found: $SRC" && exit 1
DST="$(dirname "$0")/../docs/screenshots/$NAME"
cp "$SRC" "$DST"
echo "OK: $DST"
echo "Next:"
echo "  cd ~/aura_project && git add docs/screenshots/$NAME && git commit -m 'docs: screenshot $NAME' && git push"
