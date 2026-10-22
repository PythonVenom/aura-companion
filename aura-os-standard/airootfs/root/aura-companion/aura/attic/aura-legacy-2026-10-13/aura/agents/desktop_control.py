"""Desktop Control — рабочие столы KDE Plasma 6 (X11).

Управление виртуальными рабочими столами:
  «Аура, следующий рабочий стол»
  «Аура, переключись на 3»
  «Аура, сколько рабочих столов?»

Backend: qdbus (KWin) → wmctrl → xdotool.

Наука: Licklider 1960 (симбиоз — машина служит человеку).
"""

from __future__ import annotations

import contextlib
import re
import shutil
import subprocess

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


# ── Backend: KDE Plasma 6 ────────────────────────────────
def next_desktop() -> bool:
    """Следующий рабочий стол."""
    # KDE Plasma 6 через qdbus
    if _has("qdbus6"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["qdbus6", "org.kde.KWin", "/KWin",
                 "org.kde.KWin.nextDesktop"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                return True
    if _has("qdbus"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["qdbus", "org.kde.KWin", "/KWin",
                 "org.kde.KWin.nextDesktop"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                return True
    # Fallback: wmctrl / xdotool (X11)
    if _has("wmctrl"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["wmctrl", "-d"], capture_output=True, text=True, timeout=3,
            )
            cur = -1
            for line in r.stdout.splitlines():
                if "*" in line.split()[0:3]:
                    cur = int(line.split()[0], 0)
                    break
            subprocess.run(["wmctrl", "-s", str(cur + 1)], timeout=3)
            return True
    return False


def prev_desktop() -> bool:
    """Предыдущий рабочий стол."""
    if _has("qdbus6"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["qdbus6", "org.kde.KWin", "/KWin",
                 "org.kde.KWin.previousDesktop"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                return True
    if _has("qdbus"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["qdbus", "org.kde.KWin", "/KWin",
                 "org.kde.KWin.previousDesktop"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                return True
    return False


def goto_desktop(n: int) -> bool:
    """Перейти на рабочий стол N (0-based у KWin)."""
    # KWin хочет 0-based
    idx = max(0, n - 1)
    if _has("qdbus6"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["qdbus6", "org.kde.KWin", "/KWin",
                 "org.kde.KWin.setCurrentDesktop", str(idx)],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0:
                return True
    if _has("wmctrl"):
        with contextlib.suppress(Exception):
            subprocess.run(["wmctrl", "-s", str(idx)], timeout=3)
            return True
    return False


def count_desktops() -> int:
    """Сколько рабочих столов."""
    if _has("qdbus6"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["qdbus6", "org.kde.KWin", "/KWin",
                 "org.kde.KWin.desktopCount"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0 and r.stdout.strip().isdigit():
                return int(r.stdout.strip())
    if _has("wmctrl"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["wmctrl", "-d"], capture_output=True, text=True, timeout=3,
            )
            return len(r.stdout.splitlines())
    return -1


def current_desktop() -> int:
    """Текущий рабочий стол (1-based)."""
    if _has("wmctrl"):
        with contextlib.suppress(Exception):
            r = subprocess.run(
                ["wmctrl", "-d"], capture_output=True, text=True, timeout=3,
            )
            for line in r.stdout.splitlines():
                parts = line.split()
                if parts and "*" in parts[0:3]:
                    return int(parts[0], 0) + 1
    return -1


# ── Агент ──────────────────────────────────────────────
class AgentDesktopControl(MicroAgent):
    """Управление рабочими столами KDE."""

    KEYWORDS = (
        "следующий стол", "следующий рабочий",
        "предыдущий стол", "предыдущий рабочий",
        "рабочий стол", "переключись на",
    )

    def __init__(self):
        super().__init__("desktop_control", "Рабочие столы KDE")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text.lower()

        if "следующий" in text or "вправо" in text:
            ok = next_desktop()
            return AgentResponse.ok(
                "🖥 Переключил вправо" if ok else "❌ Не смогла",
                self.name,
            )

        if "предыдущий" in text or "влево" in text or "назад" in text:
            ok = prev_desktop()
            return AgentResponse.ok(
                "🖥 Переключил влево" if ok else "❌ Не смогла",
                self.name,
            )

        # Точный номер
        m = re.search(r"(?:рабочий стол|переключись на)\s+(\d+)", text)
        if m:
            n = int(m.group(1))
            ok = goto_desktop(n)
            return AgentResponse.ok(
                f"🖥 Рабочий стол {n}" if ok else f"❌ Не смогла перейти на {n}",
                self.name,
            )

        # Сколько столов
        if "сколько" in text:
            cnt = count_desktops()
            cur = current_desktop()
            return AgentResponse.ok(
                f"🖥 Рабочих столов: {cnt}, сейчас на {cur}",
                self.name,
            )

        return AgentResponse.ok(
            "Команды: следующий стол, предыдущий стол, "
            "переключись на N, сколько столов",
            self.name,
        )


__all__ = [
    "AgentDesktopControl",
    "count_desktops", "current_desktop",
    "goto_desktop", "next_desktop", "prev_desktop",
]
