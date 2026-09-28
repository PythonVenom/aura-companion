"""Figma wrapper — REST API (ADR-037).

Figma REST API: https://api.figma.com/v1/
Token: FIGMA_TOKEN env или ~/.config/aura/figma_token
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from aura.wrappers.base import AppWrapper, WrapperError


class FigmaWrapper(AppWrapper):
    """Обёртка над Figma REST API.

    Безопасные: list_files, get_file, list_projects, export_png.
    Опасные: delete_file (требует confirm).
    """

    name = "figma"
    version = "1.0"
    transport = "rest"
    BASE = "https://api.figma.com/v1"

    SAFE = frozenset({
        "list_projects", "get_file", "list_components", "export_png",
    })

    def __init__(self, token: str | None = None) -> None:
        super().__init__()
        self.token = token or self._load_token()
        self._safe_commands = self.SAFE

    @staticmethod
    def _load_token() -> str:
        env = os.environ.get("FIGMA_TOKEN")
        if env:
            return env
        p = Path.home() / ".config" / "aura" / "figma_token"
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
        return ""

    def is_available(self) -> bool:
        return bool(self.token)

    def connect(self) -> bool:
        if not self.token:
            raise WrapperError("Figma token не найден (FIGMA_TOKEN или ~/.config/aura/figma_token)")
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def _request(self, path: str) -> dict:
        req = urllib.request.Request(
            f"{self.BASE}{path}",
            headers={"X-Figma-Token": self.token},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise WrapperError(f"Figma HTTP {e.code}: {e.reason}") from e
        except Exception as e:
            raise WrapperError(f"Figma: {e}") from e

    def execute(self, cmd: str, params: dict[str, Any] | None = None) -> dict:
        if not self.is_safe(cmd):
            raise WrapperError(f"Команда {cmd!r} требует confirm")
        params = params or {}
        try:
            if cmd == "list_projects":
                team_id = params.get("team_id", "")
                if not team_id:
                    raise WrapperError("нужен team_id")
                return {"ok": True, "result": self._request(f"/teams/{team_id}/projects")}
            if cmd == "get_file":
                key = params.get("key", "")
                if not key:
                    raise WrapperError("нужен key файла")
                return {"ok": True, "result": self._request(f"/files/{key}")}
            if cmd == "list_components":
                key = params.get("key", "")
                return {"ok": True, "result": self._request(f"/files/{key}/components")}
            return {"ok": False, "error": f"unknown cmd: {cmd}"}
        except WrapperError as e:
            return {"ok": False, "error": str(e)}


__all__ = ["FigmaWrapper"]
