"""AgentVision — скриншоты + OCR (GAPS #40, #41).

Wayland: grim (wlroots/Swayland/Hyprland)
X11:     scrot или pyautogui
OCR:     tesseract (rus+eng)

Наука:
- W3C WCAG 2.2 AA (accessibility) — текст с экрана для незрячих
- Lazar 2017 — accessibility для elder-care
- Smith 2007 (Tesseract OCR) — open-source OCR
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_session() -> str:
    """Определить сессию: 'wayland' | 'x11'."""
    xdg = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if xdg == "wayland":
        return "wayland"
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


class AgentVision(BaseAgent):
    """Скриншот + OCR (Wayland/X11)."""

    name = "vision"

    KEYWORDS = (
        "скриншот", "сделай снимок", "снимок экрана", "скрин",
        "прочитай экран", "что на экране", "распознай текст",
        "ocr", "прочти экран",
    )

    CACHE_DIR = Path.home() / ".cache" / "aura"
    SHOT_PATH = CACHE_DIR / "screenshot.png"

    def __init__(self) -> None:
        self.session = _detect_session()
        self.has_grim = shutil.which("grim") is not None
        self.has_scrot = shutil.which("scrot") is not None
        self.has_tesseract = shutil.which("tesseract") is not None
        self.has_pyautogui = False
        try:
            import pyautogui  # noqa
            self.has_pyautogui = True
        except Exception:
            pass

    # === API ===

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text.lower()

        # OCR-режим: «прочитай экран», «что на экране»
        if any(k in text for k in ("прочитай экран", "что на экране",
                                    "распознай текст", "ocr", "прочти экран")):
            shot = self._screenshot()
            if not shot.ok:  # type: ignore[truthy-function]
                return shot
            return self._ocr(shot.text)  # type: ignore[arg-type]

        # Обычный скриншот
        return self._screenshot()

    # === Логика ===

    def _screenshot(self) -> AgentResponse:
        """Сделать скриншот. Возвращает AgentResponse."""
        self.SHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        shot = str(self.SHOT_PATH)

        # Wayland — grim
        if self.session == "wayland" and self.has_grim:
            return self._run_cmd(
                ["grim", shot],
                success=f"🖼 Скриншот: {shot}",
                error_prefix="grim",
            )

        # X11 — scrot
        if self.has_scrot:
            return self._run_cmd(
                ["scrot", "-o", shot],
                success=f"🖼 Скриншот: {shot}",
                error_prefix="scrot",
            )

        # Fallback — pyautogui
        if self.has_pyautogui:
            try:
                import pyautogui
                pyautogui.screenshot(shot)
                return AgentResponse.ok(f"🖼 Скриншот: {shot}", self.name)
            except Exception as e:
                return AgentResponse.ok(f"❌ pyautogui: {e}", self.name)

        return AgentResponse.ok(
            f"❌ Нет инструментов для скриншота "
            f"(session={self.session}, grim={self.has_grim}, "
            f"scrot={self.has_scrot}, pyautogui={self.has_pyautogui})",
            self.name,
        )

    def _ocr(self, shot_response: AgentResponse) -> AgentResponse:
        """Прочитать текст с последнего скриншота через tesseract."""
        if not self.has_tesseract:
            return AgentResponse.ok(
                "❌ tesseract не установлен. Установи: "
                "sudo pacman -S tesseract tesseract-data-rus",
                self.name,
            )

        shot = str(self.SHOT_PATH)
        if not self.SHOT_PATH.exists():
            return AgentResponse.ok("❌ Нет скриншота для OCR", self.name)

        try:
            r = subprocess.run(
                ["tesseract", shot, "-", "-l", "rus+eng"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                return AgentResponse.ok(
                    f"❌ tesseract: {r.stderr[:200]}", self.name,
                )
            text = r.stdout.strip()
            if not text:
                return AgentResponse.ok(
                    "🔍 Текст на экране не найден", self.name,
                )
            # Ограничим 1500 символами
            if len(text) > 1500:
                text = text[:1500] + "..."
            return AgentResponse.ok(
                f"📖 Текст с экрана:\n{text}", self.name,
            )
        except Exception as e:
            return AgentResponse.ok(f"❌ OCR: {e}", self.name)

    def _run_cmd(self, cmd: list, success: str, error_prefix: str) -> AgentResponse:
        """Запустить команду, вернуть AgentResponse."""
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return AgentResponse.ok(success, self.name)
            return AgentResponse.ok(
                f"❌ {error_prefix}: {r.stderr[:200]}", self.name,
            )
        except Exception as e:
            return AgentResponse.ok(f"❌ {error_prefix}: {e}", self.name)


__all__ = ["AgentVision"]
