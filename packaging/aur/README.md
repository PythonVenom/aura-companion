# Aura на Arch Linux (AUR)

## Установка

    yay -S aura-companion
    # или
    paru -S aura-companion

## Что поставится

- Aura (Python-пакет)
- deps: pipewire, qt6-tools, python
- optdeps: speech-dispatcher, espeak-ng, alsa-utils, firefox, ollama

## После установки

    source /usr/bin/aura-env 2>/dev/null || true
    python -m aura            # запуск

## Ручная сборка

    git clone https://aur.archlinux.org/aura-companion.git
    cd aura-companion
    makepkg -si

## Наука

- PKGBUILD spec (Arch Wiki)
- PEP 517 (Python packaging)
- python-build / python-installer

## Статус

- v0.7.9: PKGBUILD готов, ждёт публикации в AUR
- Публикация — задача T-flash-4 (AuraOS) + отдельный шаг автора
