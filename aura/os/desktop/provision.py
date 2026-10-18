"""AuraOS Desktop Provisioner (Infrastructure as Code).

Reads spec.yaml and generates a valid LXQt panel.conf.
"""

import shutil
from pathlib import Path
import yaml

SPEC_PATH = Path(__file__).parent / "spec.yaml"
LXQT_CONFIG = Path.home() / ".config" / "lxqt" / "panel.conf"

def provision():
    print("Reading spec.yaml...")
    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    panel = spec.get("panel", {})
    plugins = panel.get("plugins", [])
    position = panel.get("position", "top").capitalize()
    height = panel.get("height", 32)
    icon_theme = spec.get("base", {}).get("icons", "Papirus-Dark")

    lines = [
        "[General]",
        "__userfile__=true",
        f"iconTheme={icon_theme}",
        "",
        "[panel1]",
        "alignment=-1",
        f"panelSize={height}",
        f"plugins={', '.join(plugins)}",
        f"position={position}",
        "width-percent=true",
        "width=100",
        ""
    ]

    # Генерируем секции для каждого плагина
    for p in plugins:
        lines.append(f"[{p}]")
        lines.append(f"type={p}")  # ВОТ ОНА, МАГИЯ LXQT
        if p in ("mainmenu", "taskbar"):
            lines.append("alignment=Left")
        else:
            lines.append("alignment=Right")
        lines.append("")

    # Бэкап старого конфига
    if LXQT_CONFIG.exists():
        backup = LXQT_CONFIG.with_suffix(".conf.bak")
        shutil.copy(LXQT_CONFIG, backup)
        print(f"Backup saved to {backup}")

    # Запись нового
    LXQT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    LXQT_CONFIG.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated new panel config at {LXQT_CONFIG}")
    print("Apply changes: killall lxqt-panel && lxqt-panel &")

if __name__ == "__main__":
    provision()
