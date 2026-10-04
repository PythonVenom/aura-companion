#!/usr/bin/env bash
# Aura AppImage builder (T074)
set -euo pipefail

VERSION="${1:-7.2.0}"
ARCH="$(uname -m)"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="Aura-${VERSION}-${ARCH}.AppImage"

cd "$ROOT"
APPDIR="$ROOT/packaging/appimage/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/scalable/apps"

# 1. Собрать wheel
python3 -m build --wheel --outdir "$APPDIR/usr/wheel"

# 2. venv внутри AppDir
python3 -m venv "$APPDIR/usr/venv"
"$APPDIR/usr/venv/bin/pip" install --quiet "$APPDIR/usr/wheel"/*.whl

# 3. .desktop + icon
cat > "$APPDIR/aura-companion.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Aura
Comment=Local voice AI companion
Exec=aura
Icon=aura-companion
Terminal=true
Categories=Utility;AudioVideo;Accessibility;
DESKTOP

# 4. AppRun
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/venv/bin/aura" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# 5. AppImage tool
if [ ! -f /tmp/appimagetool ]; then
    wget -q -O /tmp/appimagetool \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
    chmod +x /tmp/appimagetool
fi

ARCH="$ARCH" /tmp/appimagetool "$APPDIR" "$ROOT/$OUT"
echo "[ok] $OUT"
