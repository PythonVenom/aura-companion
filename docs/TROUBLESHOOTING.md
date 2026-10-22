# 🚑 Если всё сломалось
* Нет звука: pactl set-default-source alsa_input.pci-0000_00_1f.3.analog-stereo
* Зависла: systemctl --user restart aura.service
* Не видит MCP: cat ~/.config/aura/mcp_servers.json
