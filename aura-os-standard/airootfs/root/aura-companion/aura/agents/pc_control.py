"""PC Control — управление железом через Ауру.

Яркость (brightnessctl), громкость (wpctl/PipeWire), mute.
Уровни 0-10 → 0-100%.

Наука: Licklider 1960 (симбиоз — машина служит человеку),
       Saltzer & Schroeder 1975 (минимум привилегий).
"""

from __future__ import annotations

import contextlib
import re
import shutil
import subprocess

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


# ── Backend: яркость ───────────────────────────────────
def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def brightness_get() -> int:
    """Яркость 0-100%. Использует brightnessctl."""
    if not _has("brightnessctl"):
        return -1
    try:
        cur = subprocess.run(
            ["brightnessctl", "get"],
            capture_output=True, text=True, timeout=3,
        ).stdout.strip()
        maxv = subprocess.run(
            ["brightnessctl", "max"],
            capture_output=True, text=True, timeout=3,
        ).stdout.strip()
        if cur and maxv:
            return int(int(cur) / int(maxv) * 100)
    except Exception:
        pass
    return -1


def brightness_set(pct: int) -> bool:
    """Установить яркость 0-100%."""
    if not _has("brightnessctl"):
        return False
    pct = max(0, min(100, pct))
    with contextlib.suppress(Exception):
        subprocess.run(
            ["brightnessctl", "set", f"{pct}%"],
            timeout=3, capture_output=True,
        )
        return True
    return False


# ── Backend: громкость ─────────────────────────────────
def volume_get() -> int:
    """Громкость системы 0-100%."""
    # PipeWire (wpctl)
    if _has("wpctl"):
        with contextlib.suppress(Exception):
            out = subprocess.run(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                capture_output=True, text=True, timeout=3,
            ).stdout
            m = re.search(r"([\d.]+)", out)
            if m:
                return int(float(m.group(1)) * 100)
    # PulseAudio (pactl)
    if _has("pactl"):
        with contextlib.suppress(Exception):
            out = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True, timeout=3,
            ).stdout
            m = re.search(r"(\d+)%", out)
            if m:
                return int(m.group(1))
    return -1


def volume_set(pct: int) -> bool:
    """Установить громкость 0-100%."""
    pct = max(0, min(100, pct))
    if _has("wpctl"):
        with contextlib.suppress(Exception):
            subprocess.run(
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{pct}%"],
                timeout=3, capture_output=True,
            )
            return True
    if _has("pactl"):
        with contextlib.suppress(Exception):
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"],
                timeout=3, capture_output=True,
            )
            return True
    return False


def mute_toggle() -> bool:
    """Toggle mute."""
    if _has("wpctl"):
        with contextlib.suppress(Exception):
            subprocess.run(
                ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"],
                timeout=3, capture_output=True,
            )
            return True
    return False


# ── Агент ──────────────────────────────────────────────
class AgentPCControl(MicroAgent):
    """Управление яркостью и громкостью ПК."""

    KEYWORDS = (
        # Яркость
        "ярче", "темнее", "яркость", "ярко",
        # Системный звук (не музыка!)
        "система громче", "система тише",
        "громкость системы", "системный звук",
        "громкость пк", "звук системы",
        # Прямые команды с числами
        "громкость ",  # "громкость 5"
        "яркость ",    # "яркость 7"
        # Mute системы
        "mute система", "заглуши систему",
    )

    def __init__(self):
        super().__init__("pc_control", "Управление ПК")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text.lower()

        # ── Яркость: точное число 0-10 ──
        m = re.search(r"яркость\s+(\d+)", text)
        if m:
            raw = int(m.group(1))
            pct = raw * 10 if raw <= 10 else raw
            pct = max(0, min(100, pct))
            if brightness_set(pct):
                return AgentResponse.ok(f"🔆 Яркость: {pct}%", self.name)
            return AgentResponse.ok("❌ brightnessctl недоступен", self.name)

        # ── Ярче / темнее ──
        if "ярче" in text:
            cur = brightness_get()
            new = min(100, cur + 10) if cur >= 0 else 70
            brightness_set(new)
            return AgentResponse.ok(f"🔆 Яркость: {new}%", self.name)
        if "темнее" in text:
            cur = brightness_get()
            new = max(0, cur - 10) if cur >= 0 else 40
            brightness_set(new)
            return AgentResponse.ok(f"🔅 Яркость: {new}%", self.name)

        # ── Громкость: точное число 0-10 ──
        m = re.search(r"(громкость|звук)\s+(\d+)", text)
        if m:
            raw = int(m.group(2))
            pct = raw * 10 if raw <= 10 else raw
            pct = max(0, min(100, pct))
            if volume_set(pct):
                return AgentResponse.ok(f"🔊 Громкость: {pct}%", self.name)
            return AgentResponse.ok("❌ wpctl/pactl недоступен", self.name)

        # ── Громче / тише ──
        if "громче" in text:
            cur = volume_get()
            new = min(100, cur + 10) if cur >= 0 else 60
            volume_set(new)
            return AgentResponse.ok(f"🔊 Громкость: {new}%", self.name)
        if "тише" in text:
            cur = volume_get()
            new = max(0, cur - 10) if cur >= 0 else 30
            volume_set(new)
            return AgentResponse.ok(f"🔉 Громкость: {new}%", self.name)

        # ── Mute ──
        if "mute" in text or "мут" in text or "заглуши" in text:
            mute_toggle()
            return AgentResponse.ok("🔇 Звук переключён", self.name)

        # ── Статус ──
        if "статус" in text or "какая" in text:
            b = brightness_get()
            v = volume_get()
            return AgentResponse.ok(
                f"🔆 Яркость: {b}%  |  🔊 Громкость: {v}%",
                self.name,
            )

        return AgentResponse.ok(
            "Команды: ярче/темнее, громче/тише, "
            "яркость N, громкость N (N=0..10), mute",
            self.name,
        )


__all__ = [
    "AgentPCControl",
    "brightness_get",
    "brightness_set",
    "mute_toggle",
    "volume_get",
    "volume_set",
]
