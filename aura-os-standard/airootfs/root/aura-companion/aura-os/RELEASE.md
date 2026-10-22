# AuraOS — релизы

## Версия

SemVer: `major.minor.patch` (Preston-Werner 2011).
- **Major** — несовместимые изменения
- **Minor** — новые фичи
- **Patch** — фиксы

## Процесс релиза

1. Тег в git: `git tag -a vX.Y.Z -m "release"`
2. Push тега: `git push origin vX.Y.Z`
3. CI автоматом:
   - собирает ISO (Live + Standard)
   - считает SHA256
   - публикует GitHub Release

## Ручная сборка

    cd aura-os
    sudo ./build.sh
    VERSION=2026.10.05 GPG_KEY=<key-id> ./build-release.sh

## Артефакты

- `aura-live-YYYY.MM.DD-x86_64.iso` — демо
- `aura-standard-YYYY.MM.DD-x86_64.iso` — установка
- `*.iso.sha256` — контроль целостности (NIST FIPS 180-4)
- `*.iso.asc` — GPG подпись (RFC 4880)
- `release.json` — метаданные

## Проверка

    sha256sum -c aura-live-*.iso.sha256
    gpg --verify aura-live-*.iso.asc aura-live-*.iso
