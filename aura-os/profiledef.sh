#!/usr/bin/env bash
# Aura Live ISO — профиль archiso.
# Наука: archiso spec, squashfs, systemd-boot/GRUB.

iso_name="aura-live"
iso_label="AURA_$(date +%Y%m)"
iso_publisher="Aura Project <https://github.com/PythonVenom/aura-companion>"
iso_application="Aura Live — демо без установки"
iso_version="$(date +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux'
           'uefi.systemd-boot')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/usr/local/bin/aura-live-setup"]="0:0:755"
)
