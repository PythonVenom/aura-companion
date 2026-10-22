#!/bin/bash
# Aura Release Builder (F-024)
# Создаёт tar.gz + SHA256SUMS + GPG-подпись.
# Наука: NIST SP 800-111, Preston-Werner 2011 (SemVer), GPG docs.

set -e
VERSION=$(grep -E '^version' pyproject.toml | head -1 | cut -d'"' -f2)
OUT="dist/aura-${VERSION}"
mkdir -p "$OUT"

# Копируем код
cp -r aura scripts pyproject.toml requirements.txt README.md MANIFESTO.md LICENSE "$OUT/" 2>/dev/null || true

# Метаданные сборки
cat > "$OUT/BUILD_INFO.txt" << INFO
version: $VERSION
built:   $(date -u +%Y-%m-%dT%H:%M:%SZ)
commit:  $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
python:  $(python3 --version)
INFO

# Тарбол
cd dist
tar czf "aura-${VERSION}.tar.gz" "aura-${VERSION}"
sha256sum "aura-${VERSION}.tar.gz" > "aura-${VERSION}.tar.gz.sha256"

# GPG-подпись (если ключ есть)
if gpg --list-secret-keys 2>/dev/null | grep -q sec; then
    gpg --armor --detach-sign "aura-${VERSION}.tar.gz"
    echo "✅ GPG-подпись создана"
else
    echo "⚠️  GPG-ключ не найден — подпись пропущена"
    echo "   Создай: gpg --full-generate-key"
fi

echo "📦 Готово:"
ls -la "aura-${VERSION}.tar.gz"*
