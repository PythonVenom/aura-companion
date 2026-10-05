#!/usr/bin/env bash
# Aura Standard ISO — устанавливаемый десктоп с Aura.
# Наука: archiso, archinstall (JSON config), Calamares.

iso_name="aura-standard"
iso_label="AURA_STD_$(date +%Y%m)"
iso_publisher="Aura Project <https://github.com/PythonVenom/aura-companion>"
iso_application="Aura Standard — установка + десктоп"
iso_version="$(date +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux' 'uefi.systemd-boot')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/usr/local/bin/aura-installer"]="0:0:755"
  ["/usr/local/bin/aura-first-run"]="0:0:755"
)
