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

# Пароль для пользователя aura
read -s -p "Пароль для aura (A-Z a-z 0-9 _ -, от 6 символов): " AURA_PASS; echo
read -s -p "Повторите: " AURA_PASS2; echo
[[ "$AURA_PASS" != "$AURA_PASS2" ]] && echo "❌ Пароли не совпадают" && exit 1
[[ ! "$AURA_PASS" =~ ^[A-Za-z0-9_-]{6,}$ ]] && echo "❌ Только A-Z a-z 0-9 _ -, от 6 символов" && exit 1
read -p "Разрешить sudo без пароля? [y/N]: " allow_nopass
if [[ "$allow_nopass" == "y" || "$allow_nopass" == "Y" ]]; then
    SUDO_CMD="echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers"
else
    SUDO_CMD="echo '%wheel ALL=(ALL) ALL' >> /etc/sudoers"
fi
ROOT_PASS="$(head -c 16 /dev/urandom | base64 | tr -d '/+=' | head -c 20)"

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
pacstrap -K /mnt base linux linux-firmware python python-pip python-virtualenv \
    pipewire pipewire-pulse pipewire-audio wireplumber playerctl vlc \
    git sudo nano

genfstab -U /mnt >> /mnt/etc/fstab

# chroot
arch-chroot /mnt bash -c "
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
    hwclock --systohc
    echo 'aura-vm' > /etc/hostname
    echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen
    locale-gen
    echo 'LANG=en_US.UTF-8' > /etc/locale.conf
    echo "root:$ROOT_PASS" | chpasswd
    useradd -m -G wheel -s /bin/bash aura
    echo "aura:$AURA_PASS" | chpasswd
    $SUDO_CMD
    bootctl install
    echo 'default arch' > /boot/loader/loader.conf
    mkdir -p /boot/loader/entries
    printf 'title Arch\nlinux /vmlinuz-linux\ninitrd /initramfs-linux.img\noptions root=$PART_ROOT rw\n' > /boot/loader/entries/arch.conf
"

# Aura
echo "Копирование Aura..."
cp -r /root/aura_project /mnt/home/aura/ 2>/dev/null || true
arch-chroot /mnt bash -c "chown -R aura:aura /home/aura"

# venv + зависимости от имени aura
echo "Установка Python-зависимостей Aura..."
arch-chroot /mnt su - aura -c "
    cd ~/aura_project
    python -m venv venv
    ./venv/bin/pip install --quiet --upgrade pip
    ./venv/bin/pip install --quiet -e . 2>&1 | tail -3
" || echo "⚠️  pip install не завершён (проверьте вручную)"

# systemd user-unit (эквивалент systemctl --user enable без активной сессии)
echo "Регистрация user-service..."
arch-chroot /mnt bash -c '
    mkdir -p /home/aura/.config/systemd/user
    mkdir -p /home/aura/.config/systemd/user/default.target.wants
    cat > /home/aura/.config/systemd/user/aura.service <<UNIT
[Unit]
Description=Aura AI Companion
After=pipewire.service

[Service]
Type=simple
WorkingDirectory=/home/aura/aura_project
ExecStart=/home/aura/aura_project/venv/bin/python -m aura.bootstrap
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT
    ln -sf /home/aura/.config/systemd/user/aura.service \
        /home/aura/.config/systemd/user/default.target.wants/aura.service
    chown -R aura:aura /home/aura/.config/systemd
' 

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Установка завершена                          ║"
echo "║  Логин: aura                                  ║"
echo "║  Пароль: (заданный при установке)             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  root-пароль (сохраните): $ROOT_PASS"
echo "  sudo без пароля: $allow_nopass"
echo ""
read -p "Перезагрузить? [y/N]: " reboot
[[ "$reboot" == "y" ]] && reboot
