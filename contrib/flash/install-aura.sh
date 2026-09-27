#!/usr/bin/env bash
# Aura auto-installer (запускается с flash-образа).
# Устанавливает Arch + Aura на выбранный диск.
set -euo pipefail

echo "╔══════════════════════════════════════════════╗"
echo "║  Aura — установка                            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Доступные диски:"
lsblk -d -o NAME,SIZE,MODEL | grep -v loop
echo ""

read -p "Диск для установки (например sda): " DISK
DISK="/dev/$DISK"

[ ! -b "$DISK" ] && echo "❌ $DISK не найден" && exit 1

echo ""
echo "⚠️  ВНИМАНИЕ: $DISK будет СТЁРТ"
read -p "Продолжить? [y/N]: " ans
[[ "$ans" != "y" && "$ans" != "Y" ]] && echo "Отменено" && exit 0

# Разметка
echo "Разметка $DISK..."
parted -s "$DISK" mklabel gpt
parted -s "$DISK" mkpart primary fat32 1MiB 513MiB
parted -s "$DISK" set 1 esp on
parted -s "$DISK" mkpart primary ext4 513MiB 100%

PART_EFI="${DISK}1"
PART_ROOT="${DISK}2"

mkfs.fat -F32 "$PART_EFI"
mkfs.ext4 -F "$PART_ROOT"

mount "$PART_ROOT" /mnt
mkdir -p /mnt/boot
mount "$PART_EFI" /mnt/boot

# Базовая система
echo "Установка base..."
pacstrap -K /mnt base linux linux-firmware python python-pip git sudo nano

genfstab -U /mnt >> /mnt/etc/fstab

# chroot
arch-chroot /mnt bash -c "
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
    hwclock --systohc
    echo 'aura-vm' > /etc/hostname
    echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen
    locale-gen
    echo 'LANG=en_US.UTF-8' > /etc/locale.conf
    echo 'root:aura' | chpasswd
    useradd -m -G wheel -s /bin/bash aura
    echo 'aura:aura' | chpasswd
    echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
    bootctl install
    echo 'default arch' > /boot/loader/loader.conf
    mkdir -p /boot/loader/entries
    printf 'title Arch\nlinux /vmlinuz-linux\ninitrd /initramfs-linux.img\noptions root=$PART_ROOT rw\n' > /boot/loader/entries/arch.conf
"

# Aura
echo "Копирование Aura..."
cp -r /root/aura_project /mnt/home/aura/ 2>/dev/null || true
arch-chroot /mnt bash -c "chown -R aura:aura /home/aura"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Установка завершена                          ║"
echo "║  Логин: aura / aura                           ║"
echo "║  Пароль root: aura                            ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
read -p "Перезагрузить? [y/N]: " reboot
[[ "$reboot" == "y" ]] && reboot
