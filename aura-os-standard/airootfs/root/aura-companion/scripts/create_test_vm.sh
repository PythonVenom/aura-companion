#!/bin/bash
# Создать Mint VM для теста installer
set -e
VM_NAME="aura-mint-test"
ISO="$HOME/vms/mint-22.iso"
DISK="$HOME/vms/${VM_NAME}.qcow2"

if [ ! -f "$ISO" ]; then echo "нет ISO: $ISO"; exit 1; fi

# Удалить старую если есть
virsh destroy "$VM_NAME" 2>/dev/null || true
virsh undefine "$VM_NAME" 2>/dev/null || true
rm -f "$DISK"

# 4 ГБ RAM (тест "low" профиля), 20 ГБ диск, 2 ядра
virt-install \
    --name "$VM_NAME" \
    --memory 4096 \
    --vcpus 2 \
    --disk path="$DISK",size=20 \
    --cdrom "$ISO" \
    --graphics spice \
    --os-variant linuxmint22 \
    --network default \
    --noautoconsole

echo "VM создана: $VM_NAME"
echo "Открой virt-manager → запусти"
