"""AuraOS Desktop Provisioner (Infrastructure as Code)."""
import shutil
from pathlib import Path

import yaml

SPEC_PATH = Path(__file__).parent / "spec.yaml"
LXQT_CONFIG = Path.home() / ".config" / "lxqt" / "panel.conf"

def provision():
    print("Reading spec.yaml...")
    with open(SPEC_PATH, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    panel = spec.get("panel", {})
    plugins = panel.get("plugins", [])
    position = panel.get("position", "top").capitalize()
    height = panel.get("height", 32)
    icon_theme = spec.get("base", {}).get("icons", "Papirus-Dark")
    custom_cmds = spec.get("custom_commands", {})

    lines = [
        "[General]", "__userfile__=true", f"iconTheme={icon_theme}", "",
        "[panel1]", "alignment=-1", f"panelSize={height}",
        f"plugins={', '.join(plugins)}", f"position={position}",
        "width-percent=true", "width=100", ""
    ]

    for p in plugins:
        lines.append(f"[{p}]")
        # Для кастомных команд тип должен быть customcommand
        if p.startswith("customcommand"):
            lines.append("type=customcommand")
            cmd_data = custom_cmds.get(p, {})
            lines.append(f"command={cmd_data.get('command', 'true')}")
            lines.append(f"text={cmd_data.get('text', 'CMD')}")
        else:
            lines.append(f"type={p}")

        if p in ("mainmenu", "taskbar"):
            lines.append("alignment=Left")
        else:
            lines.append("alignment=Right")
        lines.append("")

    if LXQT_CONFIG.exists():
        shutil.copy(LXQT_CONFIG, LXQT_CONFIG.with_suffix(".conf.bak"))

    LXQT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    LXQT_CONFIG.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated new panel config at {LXQT_CONFIG}")

if __name__ == "__main__":
    provision()
