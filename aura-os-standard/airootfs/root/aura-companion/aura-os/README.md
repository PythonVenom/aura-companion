# AuraOS — Live ISO

Демо Aura без установки. Загружаешься с флешки — работаешь.

## Быстрая сборка

    sudo pacman -S archiso
    cd aura-os
    sudo ./build.sh

Готовый ISO — в `aura-os/out/aura-live-YYYY.MM.DD-x86_64.iso`.

## Запись на флешку

    sudo dd if=out/aura-live-*.iso of=/dev/sdX bs=4M status=progress oflag=sync

Где `/dev/sdX` — твоя флешка (проверь `lsblk`!).

## Что внутри

- KDE Plasma (крупный шрифт, дружелюбный UI)
- Aura предустановлена
- speech-dispatcher + espeak-ng (TTS)
- Firefox для native messaging bridge
- NetworkManager для сети

## Загрузка

- BIOS: syslinux
- UEFI: systemd-boot

## Наука

- archiso (Arch Wiki) — профиль
- squashfs (Linux 2.6) — сжатая ФС
- systemd-boot / GRUB — загрузка
- MKarchiso — сборка

## Roadmap

- v7.9: Live ISO (эта задача)
- v8.0: Aura Standard (полный десктоп + installer)
- v8.0: AuraOS (полный дистрибутив + onboarding)
