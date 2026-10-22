"""AgentClipboard — буфер обмена (GAPS #42).

Чтение, запись, watcher (фоновое отслеживание).
Безопасность: не логирует пароли/ключи (детектор секретов).

Инструменты:
- Wayland: wl-paste / wl-copy
- X11:     xclip / xsel

Наука:
- Miller 1956 (7±2) — не хранить много
- Saltzer & Schroeder 1975 (least privilege) — фильтр секретов
- OWASP (2021) — не логировать пароли
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

# Паттерны секретов (OWASP 2021)
SECRET_PATTERNS = [
    re.compile(r"password\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"passwd\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"secret\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"token\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"BEGIN\s+(RSA|OPENSSH|PGP)\s+PRIVATE\s+KEY"),
    re.compile(r"ssh-rsa\s+AAAA[A-Za-z0-9+/=]+"),
]


def _looks_like_secret(text: str) -> bool:
    """True если текст похож на пароль/токен/ключ."""
    if not text:
        return False
    return any(pat.search(text) for pat in SECRET_PATTERNS)


def _detect_session() -> str:
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


class AgentClipboard(BaseAgent):
    """Буфер обмена: чтение, запись, watcher."""

    name = "clipboard"
    description = "Буфер обмена"

    KEYWORDS = (
        "буфер",
        "в буфере",
        "из буфера",
        "скопируй",
        "вставь",
        "что скопировано",
        "что в буфере",
        "clipboard",
        "copy",
        "paste",
    )

    CACHE = Path.home() / ".cache" / "aura" / "clipboard"
    WATCH_INTERVAL = 2.0  # сек
    MAX_SIZE = 100_000    # 100 KB (Miller 1956)

    def __init__(self) -> None:
        self.session = _detect_session()
        self.has_wl = shutil.which("wl-paste") is not None
        self.has_xclip = shutil.which("xclip") is not None
        self.has_xsel = shutil.which("xsel") is not None

    # === API ===

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower().strip()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text.lower().strip()

        # Скопировать
        if text.startswith("скопируй ") or "скопируй" in text:
            what = request.text[len("скопируй"):].strip(" :.,!?")
            if not what:
                return AgentResponse.ok("❌ Что скопировать?", self.name)
            ok = self.copy(what)
            return AgentResponse.ok(
                f"📋 Скопировано ({len(what)} симв.)" if ok else "❌ Не могу скопировать",
                self.name,
            )

        # Что в буфере
        if "что в буфере" in text or "что скопировано" in text or "clipboard" in text:
            return AgentResponse.ok(self._read_summary(), self.name)

        # Вставить (просто показать)
        if "вставь" in text or "paste" in text:
            val = self.read()
            if not val:
                return AgentResponse.ok("📋 Буфер пуст", self.name)
            if _looks_like_secret(val):
                return AgentResponse.ok(
                    "🔒 В буфере похоже на пароль/токен. Не показываю (OWASP 2021)",
                    self.name,
                )
            return AgentResponse.ok(f"📋 В буфере:\n{val[:500]}", self.name)

        return AgentResponse.ok(self._read_summary(), self.name)

    # === Логика ===

    def read(self) -> str:
        """Прочитать буфер (Wayland → X11 → fallback)."""
        # Wayland
        if self.session == "wayland" and self.has_wl:
            return self._run_read(["wl-paste", "--no-newline"])
        # X11
        if self.has_xclip:
            return self._run_read(["xclip", "-selection", "clipboard", "-o"])
        if self.has_xsel:
            return self._run_read(["xsel", "-b", "-o"])
        # Fallback — wl-paste если есть
        if self.has_wl:
            return self._run_read(["wl-paste", "--no-newline"])
        return ""

    def copy(self, text: str) -> bool:
        """Записать в буфер. True при успехе."""
        if not text:
            return False
        # Ограничение размера (Miller 1956)
        if len(text) > self.MAX_SIZE:
            text = text[:self.MAX_SIZE]

        # Wayland
        if self.session == "wayland" and shutil.which("wl-copy"):
            return self._run_write(["wl-copy"], text)
        # X11
        if self.has_xclip:
            return self._run_write(["xclip", "-selection", "clipboard"], text)
        if self.has_xsel:
            return self._run_write(["xsel", "-b", "-i"], text)
        # Fallback — wl-copy
        if shutil.which("wl-copy"):
            return self._run_write(["wl-copy"], text)
        return False

    def _read_summary(self) -> str:
        """Краткая сводка о буфере (без секретов)."""
        val = self.read()
        if not val:
            return "📋 Буфер пуст"
        if _looks_like_secret(val):
            return f"🔒 В буфере {len(val)} симв., похоже на секрет (не показываю)"
        preview = val[:200].replace("\n", " ")
        return f"📋 В буфере ({len(val)} симв.): {preview}"

    def _run_read(self, cmd: list) -> str:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return r.stdout
        except Exception:
            pass
        return ""

    def _run_write(self, cmd: list, text: str) -> bool:
        try:
            r = subprocess.run(
                cmd, input=text, capture_output=True, text=True, timeout=5,
            )
            return r.returncode == 0
        except Exception:
            return False


__all__ = ["AgentClipboard", "_looks_like_secret"]
