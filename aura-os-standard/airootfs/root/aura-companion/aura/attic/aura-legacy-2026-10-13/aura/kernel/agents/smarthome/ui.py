"""Smarthome UI — text-меню ламп."""
def render(lamps: dict) -> str:
    if not lamps:
        return "Лампы не настроены."
    lines = ["💡 ЛАМПЫ:"]
    for room, l in lamps.items():
        state = "ON" if l.get("on") else "OFF"
        lines.append(f"  {room}: {state} ({l.get('brightness', 0)}%)")
    return "\n".join(lines)
