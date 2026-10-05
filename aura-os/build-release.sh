#!/usr/bin/env bash
# AuraOS Release — подпись, checksums, метаданные.
# Наука: RFC 4880 (GPG), NIST FIPS 180-4 (SHA256), SemVer.

set -euo pipefail

PROFILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${PROFILE_DIR}/out"
VERSION="${VERSION:-$(date +%Y.%m.%d)}"
GPG_KEY="${GPG_KEY:-}"

log() { printf "\033[1;34m[release]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

[ -d "$OUT_DIR" ] || die "Сначала собери ISO (./build.sh)"

log "Сборка релиза AuraOS $VERSION"

# 1. SHA256 checksums
cd "$OUT_DIR"
for iso in *.iso; do
    [ -f "$iso" ] || continue
    log "SHA256: $iso"
    sha256sum "$iso" > "${iso}.sha256"
done

# 2. GPG подпись (если ключ задан)
if [ -n "$GPG_KEY" ]; then
    for iso in *.iso; do
        [ -f "$iso" ] || continue
        log "GPG: $iso"
        gpg --default-key "$GPG_KEY" --detach-sign --armor "$iso"
    done
    log "Публичный ключ:"
    gpg --armor --export "$GPG_KEY" > "$OUT_DIR/aura-os-public.key"
fi

# 3. Метаданные релиза
cat > "$OUT_DIR/release.json" <<JSON
{
  "version": "$VERSION",
  "iso_files": $(ls *.iso 2>/dev/null | jq -R . | jq -s .),
  "sha256_files": $(ls *.sha256 2>/dev/null | jq -R . | jq -s .),
  "gpg_signed": $([ -n "$GPG_KEY" ] && echo true || echo false),
  "built_at": "$(date -Iseconds)",
  "builder": "$(uname -n)"
}
JSON

log "Готово. Артефакты в $OUT_DIR:"
ls -lh "$OUT_DIR"/*.iso "$OUT_DIR"/*.sha256 "$OUT_DIR"/release.json 2>/dev/null
